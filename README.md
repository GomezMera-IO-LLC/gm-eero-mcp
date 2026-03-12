# eero MCP Server

An MCP (Model Context Protocol) server for managing your eero WiFi network. This server provides tools to monitor and control your eero mesh network through AI assistants.

## Features

- 🔐 Login with phone number or email
- 📱 SMS/Email verification support
- 🌐 List all networks in your account
- 📊 Get detailed network information
- 💻 List connected devices
- 🔄 Reboot networks remotely
- 💾 Automatic session management

## Installation

```bash
# Install using uv (recommended)
uv pip install -e eero-mcp-server

# Or using pip
pip install -e eero-mcp-server
```

## Configuration

Add to your Kiro MCP configuration file (`.kiro/settings/mcp.json` or `~/.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "eero": {
      "command": "python",
      "args": ["-m", "eero_mcp_server"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Or if installed with uvx:

```json
{
  "mcpServers": {
    "eero": {
      "command": "uvx",
      "args": ["eero-mcp-server"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Usage

### First Time Setup

1. Use `eero_login` with your phone number or email
2. Check your phone/email for verification code
3. Use `eero_verify` with the code
4. Session is automatically saved for future use

### Available Tools

- `eero_login` - Initiate login with phone/email
- `eero_verify` - Complete login with verification code
- `eero_get_account` - Get full account information
- `eero_list_networks` - List all your eero networks
- `eero_get_network` - Get details about a specific network
- `eero_list_devices` - List devices connected to a network
- `eero_list_eeros` - List all eero hardware devices (routers/access points) in a network
- `eero_update_device_nickname` - Update the nickname of a connected device
- `eero_reboot_network` - Reboot entire network
- `eero_reboot_eero` - Reboot a specific eero device
- `eero_list_profiles` - List all profiles in a network
- `eero_create_profile` - Create a new profile
- `eero_update_profile` - Update profile settings (name, pause status)
- `eero_delete_profile` - Delete a profile
- `eero_assign_device_to_profile` - Assign a device to a profile (⚠️ See Known Limitations)

### Example Commands

Ask your AI assistant:

- "Login to my eero account with +1234567890"
- "Verify my eero login with code 123456"
- "List all my eero networks"
- "Show me devices connected to my home network"
- "List all profiles in my network"
- "Create a new profile called 'Guest Devices'"
- "Rename the device at /2.2/devices/12345 to 'Living Room TV'"
- "Reboot my eero network"

## Known Limitations

### Device Profile Assignment
The `eero_assign_device_to_profile` tool has a known limitation with the eero API:
- The API accepts profile assignment requests and returns HTTP 200 success responses
- However, the assignments **do not persist** - devices remain in their original profiles
- This appears to be a limitation of the eero backend API, not the implementation
- Multiple approaches have been tested (different endpoints, payload formats) with the same result
- Profile creation, updates, deletion, and listing all work correctly
- Device nickname updates work correctly

**Workaround:** Device profile assignments must be done through the official eero mobile app.

## Notes

- Session tokens are stored in `~/.eero_session.json`
- This uses an unofficial eero API (reverse-engineered from the mobile app)
- Does not support Amazon account login (phone/email only)
- Network URLs are provided by `eero_list_networks` and used in other commands

## Credits

Based on the unofficial [eero-client](https://github.com/343max/eero-client) Python library.
