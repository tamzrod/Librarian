# Plugin Lifecycle States

**Version**: 1.0  
**Last Updated**: 2026-07-05

---

## Overview

Librarian plugins have a defined lifecycle that tracks their availability and operational state. This document defines the official states, their meanings, and expected UI behavior.

## State Definitions

### 1. Available

**Description**: Plugin exists in the codebase and has a registered handler. All dependencies are installed and the plugin is ready to process jobs.

**Indicators**:
- Handler registered in worker
- Required packages installed
- Database schema ready (if applicable)

**UI Behavior**:
- Badge: Green "Enabled"
- Toggle: Functional
- Actions: Can enable/disable

```
┌─────────────────────────────┐
│ Object Detection            │
│ Status: Enabled            │
│ ┌─────────────────────────┐ │
│ │ [🔘 Toggle]             │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

---

### 2. Installed

**Description**: Plugin code exists and is registered, but not yet enabled for processing.

**Indicators**:
- Handler registered
- Dependencies satisfied
- Not enabled in configuration

**UI Behavior**:
- Badge: Gray "Disabled"
- Toggle: Functional
- Actions: Can enable

```
┌─────────────────────────────┐
│ OCR                        │
│ Status: Disabled           │
│ ┌─────────────────────────┐ │
│ │ [  Toggle]              │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

---

### 3. Enabled

**Description**: Plugin is active and will receive jobs for matching artifact types.

**Indicators**:
- `enabled: true` in configuration
- All dependencies available
- Handler registered

**UI Behavior**:
- Badge: Green "Enabled"
- Toggle: On position
- Jobs scheduled for this plugin

---

### 4. Disabled

**Description**: Plugin code exists but is not processing jobs.

**Indicators**:
- `enabled: false` in configuration
- Handler exists but not called
- Can be re-enabled

**UI Behavior**:
- Badge: Gray "Disabled"
- Toggle: Off position
- No jobs scheduled

---

### 5. Missing Dependencies ⚠️

**Description**: Plugin code exists and would be functional, but required packages are not installed.

**Indicators**:
- Handler registered
- `required_packages` defined
- One or more packages not importable

**Example**:
```
┌─────────────────────────────┐
│ Object Detection           │
│ Status: Missing Dependencies│
│ ┌─────────────────────────┐ │
│ │ [  Toggle]              │ │
│ └─────────────────────────┘ │
│ Requires:                   │
│   [ultralytics]             │
└─────────────────────────────┘
```

**UI Behavior**:
- Badge: Orange "Missing Dependencies"
- Toggle: Disabled (cannot enable without dependencies)
- Shows required packages list
- Links to installation instructions

**Why This State Exists**:
- Provides visibility into plugin capabilities
- Guides users toward installation steps
- Prevents confusion about why plugin doesn't work

---

### 6. Error

**Description**: Plugin encountered an error during initialization or processing.

**Indicators**:
- Handler registered
- Exception occurred
- Cannot process jobs

**Example**:
```
┌─────────────────────────────┐
│ Embeddings                 │
│ Status: Error              │
│ ┌─────────────────────────┐ │
│ │ [  Toggle]              │ │
│ └─────────────────────────┘ │
│ ⚠️ OpenAI API key not set  │
└─────────────────────────────┘
```

**UI Behavior**:
- Badge: Red "Error"
- Toggle: Disabled
- Shows error message
- Suggests remediation steps

---

### 7. Not Implemented

**Description**: Plugin is defined in the registry but has no handler implementation.

**Indicators**:
- Definition in `PLUGIN_DEFINITIONS`
- No handler registered
- Planned but not coded

**UI Behavior**:
- Badge: Gray "Not Implemented"
- Toggle: Disabled
- Shows "Handler not implemented" message
- May link to development roadmap

---

### 8. Deprecated

**Description**: Plugin exists but is marked for removal in a future version.

**Indicators**:
- Deprecation notice in code
- Migration path exists
- Will be removed in version X.Y

**UI Behavior**:
- Badge: Yellow "Deprecated"
- Toggle: May be disabled
- Shows deprecation notice
- Links to replacement plugin

---

## State Transition Diagram

```
                    ┌──────────────┐
                    │ Not Impl     │ (definition only)
                    └──────┬───────┘
                           │ implement
                           ▼
                    ┌──────────────┐
         ┌─────────│ Available    │◄─────────┐
         │         └──────┬───────┘          │
         │                │ dependencies OK  │
         │                ▼                  │
         │         ┌──────────────┐          │
         │         │ Missing Deps │          │ install
         │         └──────┬───────┘          │ deps
         │                │                  │
         │         ┌──────┴───────┐          │
         │         ▼              │          │
         │  ┌──────────┐   ┌──────┴───────┐  │
         │  │ Disabled │   │ Enabled      │  │
         │  └───┬──────┘   └──────┬───────┘  │
         │      │ enable           │ disable │
         │      └────────┬─────────┘          │
         │               ▼                   │
         │        ┌──────────┐               │
         │        │ Error   │───────────────┘
         │        └──────────┘ error occurs
         │
         │ deprecate
         ▼
   ┌──────────┐
   │Deprecated │
   └──────────┘
```

## Status Field in API

The API exposes plugin status as a string:

```json
{
  "name": "object_detection",
  "enabled": false,
  "status": "missing_dependencies",
  "missing_dependencies": ["ultralytics"],
  "error_message": "Missing packages: ultralytics"
}
```

### Status Values

| Status String | Badge Color | Can Toggle | Description |
|--------------|-------------|------------|-------------|
| `enabled` | Green | Yes | Ready to process |
| `disabled` | Gray | Yes | Installed but off |
| `missing_dependencies` | Orange | No | Needs packages |
| `error` | Red | No | Has errors |
| `not_implemented` | Gray | No | No handler |
| `deprecated` | Yellow | Varies | Marked for removal |

## UI Component States

### Badge Component

```tsx
const statusConfig = {
  enabled: { label: 'Enabled', className: 'enabled' },
  disabled: { label: 'Disabled', className: 'disabled' },
  missing_dependencies: { label: 'Missing Dependencies', className: 'warning' },
  error: { label: 'Error', className: 'error' },
  not_implemented: { label: 'Not Implemented', className: 'disabled' },
  deprecated: { label: 'Deprecated', className: 'warning' },
}
```

### Toggle Behavior

| Status | Toggle Enabled | Toggle Behavior |
|--------|----------------|-----------------|
| `enabled` | Yes | Can disable |
| `disabled` | Yes | Can enable |
| `missing_dependencies` | No | Shows tooltip explaining why |
| `error` | No | Shows error details |
| `not_implemented` | No | Informational only |
| `deprecated` | Varies | May allow disable only |

## Implementation Notes

### Registry Detection

The plugin status is determined at startup by `_discover_all_plugins()`:

```python
def _discover_all_plugins() -> dict:
    for plugin_name, defn in PLUGIN_DEFINITIONS.items():
        required_packages = defn.get('required_packages', [])
        
        if required_packages:
            missing = _check_missing_packages(required_packages)
            if missing:
                status = PluginStatus.MISSING_DEPENDENCIES
            else:
                status = PluginStatus.ENABLED
        else:
            status = PluginStatus.ENABLED
    
    return status_info
```

### Handler Availability Check

Plugins without handlers are marked `not_implemented`:

```python
if job_type not in registered_job_types:
    plugin_status[plugin_name] = {
        'status': PluginStatus.DISABLED,
        'error_message': 'Plugin handler not implemented'
    }
```

---

*This document defines the official plugin lifecycle states for Librarian.*
