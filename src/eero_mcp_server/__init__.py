"""MCP server for managing eero WiFi networks."""

import os
import json
import requests
from typing import Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from eero import Eero
from eero.session import SessionStorage

app = Server("eero-mcp-server")

# Session file location
session_file = os.path.expanduser("~/.eero_session.json")


class FileSessionStorage(SessionStorage):
    """Session storage that persists to a file."""
    
    def __init__(self, session_file: str):
        self.session_file = session_file
        self._cookie: Optional[str] = None
        self._load()
    
    def _load(self):
        """Load session from file."""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    self._cookie = data.get('cookie')
            except Exception:
                pass
    
    def _save(self):
        """Save session to file."""
        with open(self.session_file, 'w') as f:
            json.dump({'cookie': self._cookie}, f)
    
    @property
    def cookie(self) -> Optional[str]:
        """Get the session cookie."""
        return self._cookie
    
    @cookie.setter
    def cookie(self, value: Optional[str]):
        """Set the session cookie and save to file."""
        self._cookie = value
        self._save()


# Global eero client instance
eero_client = None
pending_user_token = None  # Store user_token between login and verify


def get_eero_client() -> Eero:
    """Get or create eero client with session management."""
    global eero_client
    
    if eero_client is None:
        session = FileSessionStorage(session_file)
        eero_client = Eero(session)
    
    return eero_client


def eero_api_put(url_path: str, json_data: dict, cookie: str) -> dict:
    """Make a PUT request to the eero API."""
    api_endpoint = f"https://api-user.e2ro.com/2.2/{url_path}"
    response = requests.put(api_endpoint, json=json_data, cookies={'s': cookie})
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    
    # Check if response has the expected meta structure
    if 'meta' in data and 'code' in data['meta']:
        if data['meta']['code'] not in [200, 201]:
            raise Exception(f"API Error: {data['meta'].get('error', 'Unknown error')}")
    
    return data.get('data', data)


def eero_api_post(url_path: str, json_data: dict, cookie: str) -> dict:
    """Make a POST request to the eero API."""
    api_endpoint = f"https://api-user.e2ro.com/2.2/{url_path}"
    response = requests.post(api_endpoint, json=json_data, cookies={'s': cookie})
    response.raise_for_status()
    data = response.json()
    
    if 'meta' in data and 'code' in data['meta']:
        if data['meta']['code'] not in [200, 201]:
            raise Exception(f"API Error: {data['meta'].get('error', 'Unknown error')}")
    
    return data.get('data', data)


def eero_api_delete(url_path: str, cookie: str) -> dict:
    """Make a DELETE request to the eero API."""
    api_endpoint = f"https://api-user.e2ro.com/2.2/{url_path}"
    response = requests.delete(api_endpoint, cookies={'s': cookie})
    response.raise_for_status()
    
    # DELETE might return empty response
    if response.text:
        data = response.json()
        if 'meta' in data and 'code' in data['meta']:
            if data['meta']['code'] not in [200, 201, 204]:
                raise Exception(f"API Error: {data['meta'].get('error', 'Unknown error')}")
        return data.get('data', data)
    
    return {"success": True}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available eero management tools."""
    return [
        Tool(
            name="eero_login",
            description="Login to eero account using phone number or email. Returns verification required status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Phone number or email address for eero account"
                    }
                },
                "required": ["identifier"]
            }
        ),
        Tool(
            name="eero_verify",
            description="Verify login with SMS/email code received after login attempt",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Verification code from SMS or email"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="eero_get_account",
            description="Get account information including all networks",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="eero_list_networks",
            description="List all eero networks in the account",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="eero_get_network",
            description="Get detailed information about a specific network",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_url": {
                        "type": "string",
                        "description": "Network URL from list_networks"
                    }
                },
                "required": ["network_url"]
            }
        ),
        Tool(
            name="eero_list_devices",
            description="List all devices connected to a network",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_url": {
                        "type": "string",
                        "description": "Network URL from list_networks"
                    }
                },
                "required": ["network_url"]
            }
        ),
        Tool(
            name="eero_list_eeros",
            description="List all eero devices (routers/access points) in a network with their status and details",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_url": {
                        "type": "string",
                        "description": "Network URL from list_networks"
                    }
                },
                "required": ["network_url"]
            }
        ),
        Tool(
            name="eero_reboot_network",
            description="Reboot an eero network",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_url": {
                        "type": "string",
                        "description": "Network URL from list_networks"
                    }
                },
                "required": ["network_url"]
            }
        ),
        Tool(
            name="eero_reboot_eero",
            description="Reboot a specific eero device (router/access point)",
            inputSchema={
                "type": "object",
                "properties": {
                    "eero_id": {
                        "type": "string",
                        "description": "Eero device ID from list_eeros"
                    }
                },
                "required": ["eero_id"]
            }
        ),
        Tool(
            name="eero_update_device_nickname",
            description="Update the nickname of a device connected to the network",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_url": {
                        "type": "string",
                        "description": "Device URL from list_devices (e.g., '/2.2/devices/12345')"
                    },
                    "nickname": {
                        "type": "string",
                        "description": "New nickname for the device"
                    }
                },
                "required": ["device_url", "nickname"]
            }
        ),
        Tool(
            name="eero_list_profiles",
            description="List all profiles in a network. Profiles are used to organize and manage devices.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_url": {
                        "type": "string",
                        "description": "Network URL from list_networks"
                    }
                },
                "required": ["network_url"]
            }
        ),
        Tool(
            name="eero_create_profile",
            description="Create a new profile in a network",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_url": {
                        "type": "string",
                        "description": "Network URL from list_networks"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the new profile"
                    }
                },
                "required": ["network_url", "name"]
            }
        ),
        Tool(
            name="eero_update_profile",
            description="Update a profile's settings (name, pause status, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_url": {
                        "type": "string",
                        "description": "Profile URL from list_profiles (e.g., '/2.2/networks/12345/profiles/67890')"
                    },
                    "name": {
                        "type": "string",
                        "description": "New name for the profile (optional)"
                    },
                    "paused": {
                        "type": "boolean",
                        "description": "Pause or unpause internet access for this profile (optional)"
                    }
                },
                "required": ["profile_url"]
            }
        ),
        Tool(
            name="eero_delete_profile",
            description="Delete a profile from the network",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_url": {
                        "type": "string",
                        "description": "Profile URL from list_profiles (e.g., '/2.2/networks/12345/profiles/67890')"
                    }
                },
                "required": ["profile_url"]
            }
        ),
        Tool(
            name="eero_assign_device_to_profile",
            description="Assign a device to a specific profile",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_url": {
                        "type": "string",
                        "description": "Device URL from list_devices (e.g., '/2.2/devices/12345')"
                    },
                    "profile_url": {
                        "type": "string",
                        "description": "Profile URL from list_profiles (e.g., '/2.2/networks/12345/profiles/67890')"
                    }
                },
                "required": ["device_url", "profile_url"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for eero management."""
    global pending_user_token
    client = get_eero_client()
    
    try:
        if name == "eero_login":
            identifier = arguments["identifier"]
            user_token = client.login(identifier)
            pending_user_token = user_token  # Store for verification step
            return [TextContent(
                type="text",
                text=f"Login initiated. Check your phone/email for verification code.\n\nUse eero_verify with the code you receive."
            )]
        
        elif name == "eero_verify":
            code = arguments["code"]
            if not pending_user_token:
                return [TextContent(
                    type="text",
                    text="Error: No pending login. Please call eero_login first."
                )]
            response = client.login_verify(code, pending_user_token)
            pending_user_token = None  # Clear after use
            return [TextContent(
                type="text",
                text=f"Login verified successfully! Session saved.\nYou can now use other eero commands."
            )]
        
        elif name == "eero_get_account":
            account = client.account()
            return [TextContent(
                type="text",
                text=json.dumps(account, indent=2)
            )]
        
        elif name == "eero_list_networks":
            account = client.account()
            networks = account.get('networks', {}).get('data', [])
            network_list = [
                {
                    'name': net.get('name'),
                    'url': net.get('url'),
                    'status': net.get('status')
                }
                for net in networks
            ]
            return [TextContent(
                type="text",
                text=json.dumps(network_list, indent=2)
            )]
        
        elif name == "eero_get_network":
            network_url = arguments["network_url"]
            network_info = client.networks(network_url)
            return [TextContent(
                type="text",
                text=json.dumps(network_info, indent=2)
            )]
        
        elif name == "eero_list_devices":
            network_url = arguments["network_url"]
            devices = client.devices(network_url)
            return [TextContent(
                type="text",
                text=json.dumps(devices, indent=2)
            )]
        
        elif name == "eero_list_eeros":
            network_url = arguments["network_url"]
            eeros = client.eeros(network_url)
            return [TextContent(
                type="text",
                text=json.dumps(eeros, indent=2)
            )]
        
        elif name == "eero_reboot_network":
            network_url = arguments["network_url"]
            # Get the first eero in the network to reboot
            network_info = client.networks(network_url)
            eeros = network_info.get('eeros', {}).get('data', [])
            if not eeros:
                return [TextContent(
                    type="text",
                    text="Error: No eero devices found in network"
                )]
            # Reboot the gateway (first eero)
            gateway_url = eeros[0].get('url')
            result = client.reboot(gateway_url)
            return [TextContent(
                type="text",
                text=f"Network reboot initiated via gateway.\nResponse: {json.dumps(result, indent=2)}"
            )]
        
        elif name == "eero_reboot_eero":
            eero_id = arguments["eero_id"]
            result = client.reboot(eero_id)
            return [TextContent(
                type="text",
                text=f"Eero device reboot initiated.\nResponse: {json.dumps(result, indent=2)}"
            )]
        
        elif name == "eero_update_device_nickname":
            device_url = arguments["device_url"]
            nickname = arguments["nickname"]
            
            # Get session cookie
            if client.needs_login():
                return [TextContent(
                    type="text",
                    text="Error: Not logged in. Please login first."
                )]
            
            # Make PUT request to update device using the full device URL path
            # Remove the leading /2.2/ if present since we'll add it in the API call
            url_path = device_url
            if url_path.startswith('/2.2/'):
                url_path = url_path[5:]  # Remove '/2.2/' prefix
            
            try:
                result = eero_api_put(
                    url_path,
                    {"nickname": nickname},
                    client.session.cookie
                )
                return [TextContent(
                    type="text",
                    text=f"Device nickname updated successfully to '{nickname}'.\nResponse: {json.dumps(result, indent=2)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error updating device nickname: {str(e)}"
                )]
        
        elif name == "eero_list_profiles":
            network_url = arguments["network_url"]
            
            if client.needs_login():
                return [TextContent(
                    type="text",
                    text="Error: Not logged in. Please login first."
                )]
            
            # Make a direct GET request to the profiles endpoint
            url_path = network_url
            if url_path.startswith('/2.2/'):
                url_path = url_path[5:]
            
            # Add /profiles to the path
            profiles_url = f"{url_path}/profiles"
            
            try:
                # Make GET request to profiles endpoint
                api_endpoint = f"https://api-user.e2ro.com/2.2/{profiles_url}"
                response = requests.get(api_endpoint, cookies={'s': client.session.cookie})
                response.raise_for_status()
                data = response.json()
                
                # Handle both list and dict responses
                if isinstance(data, list):
                    profiles = data
                else:
                    profiles = data.get('data', [])
                
                profile_list = []
                for profile in profiles:
                    # Safely get device count
                    devices = profile.get('devices', [])
                    if isinstance(devices, dict):
                        device_count = len(devices.get('data', []))
                    elif isinstance(devices, list):
                        device_count = len(devices)
                    else:
                        device_count = 0
                    
                    profile_list.append({
                        'name': profile.get('name'),
                        'url': profile.get('url'),
                        'paused': profile.get('paused', False),
                        'device_count': device_count,
                        'default': profile.get('default', False)
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps(profile_list, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error listing profiles: {str(e)}"
                )]
        
        elif name == "eero_create_profile":
            network_url = arguments["network_url"]
            name = arguments["name"]
            
            if client.needs_login():
                return [TextContent(
                    type="text",
                    text="Error: Not logged in. Please login first."
                )]
            
            # Remove /2.2/ prefix if present
            url_path = network_url
            if url_path.startswith('/2.2/'):
                url_path = url_path[5:]
            
            # Add /profiles to the path
            url_path = f"{url_path}/profiles"
            
            try:
                result = eero_api_post(
                    url_path,
                    {"name": name},
                    client.session.cookie
                )
                return [TextContent(
                    type="text",
                    text=f"Profile '{name}' created successfully.\nResponse: {json.dumps(result, indent=2)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error creating profile: {str(e)}"
                )]
        
        elif name == "eero_update_profile":
            profile_url = arguments["profile_url"]
            
            if client.needs_login():
                return [TextContent(
                    type="text",
                    text="Error: Not logged in. Please login first."
                )]
            
            # Build update data
            update_data = {}
            if "name" in arguments:
                update_data["name"] = arguments["name"]
            if "paused" in arguments:
                update_data["paused"] = arguments["paused"]
            
            if not update_data:
                return [TextContent(
                    type="text",
                    text="Error: No update parameters provided. Specify 'name' or 'paused'."
                )]
            
            # Remove /2.2/ prefix if present
            url_path = profile_url
            if url_path.startswith('/2.2/'):
                url_path = url_path[5:]
            
            try:
                result = eero_api_put(
                    url_path,
                    update_data,
                    client.session.cookie
                )
                return [TextContent(
                    type="text",
                    text=f"Profile updated successfully.\nResponse: {json.dumps(result, indent=2)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error updating profile: {str(e)}"
                )]
        
        elif name == "eero_delete_profile":
            profile_url = arguments["profile_url"]
            
            if client.needs_login():
                return [TextContent(
                    type="text",
                    text="Error: Not logged in. Please login first."
                )]
            
            # Remove /2.2/ prefix if present
            url_path = profile_url
            if url_path.startswith('/2.2/'):
                url_path = url_path[5:]
            
            try:
                result = eero_api_delete(
                    url_path,
                    client.session.cookie
                )
                return [TextContent(
                    type="text",
                    text=f"Profile deleted successfully.\nResponse: {json.dumps(result, indent=2)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error deleting profile: {str(e)}"
                )]
        
        elif name == "eero_assign_device_to_profile":
            device_url = arguments["device_url"]
            profile_url = arguments["profile_url"]
            
            if client.needs_login():
                return [TextContent(
                    type="text",
                    text="Error: Not logged in. Please login first."
                )]
            
            # Remove /2.2/ prefix if present from device URL
            url_path = device_url
            if url_path.startswith('/2.2/'):
                url_path = url_path[5:]
            
            try:
                # Try sending just the profile URL as a string
                result = eero_api_put(
                    url_path,
                    {"profile": profile_url},
                    client.session.cookie
                )
                return [TextContent(
                    type="text",
                    text=f"Device assigned to profile successfully.\nResponse: {json.dumps(result, indent=2)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error assigning device to profile: {str(e)}"
                )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


def main():
    """Run the MCP server."""
    import asyncio
    import mcp.server.stdio
    
    async def run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
