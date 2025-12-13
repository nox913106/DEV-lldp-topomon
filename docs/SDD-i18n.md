# Internationalization (i18n) System Documentation

## Overview

The LLDP Topology Monitor supports multiple languages through a client-side internationalization system. The system uses the `i18n.js` file to manage translations and automatically applies them to HTML elements with `data-i18n` attributes.

## Supported Languages

| Language Code | Display Name |
|--------------|--------------|
| `en` | English |
| `zh-TW` | 繁體中文 (Traditional Chinese) |
| `zh-CN` | 简体中文 (Simplified Chinese) |

## How It Works

### 1. Translation Keys

All translatable text is stored in `/static/js/i18n.js` with the following structure:

```javascript
const i18n = {
    translations: {
        'en': {
            key1: 'English text',
            key2: 'More text',
            // ...
        },
        'zh-TW': {
            key1: '繁體中文',
            key2: '更多文字',
            // ...
        },
        'zh-CN': {
            key1: '简体中文',
            key2: '更多文字',
            // ...
        }
    }
};
```

### 2. HTML Usage

Use `data-i18n` attribute on HTML elements:

```html
<span data-i18n="key1">Default English Text</span>
<button data-i18n="save">Save</button>
<label data-i18n="targetIp">Target IP</label>
```

### 3. JavaScript Usage

For dynamically generated content, use `i18n.t()`:

```javascript
alert(i18n.t('enterTargetIp'));
btn.textContent = i18n.t('testing');
html += `<div>${i18n.t('discoveryComplete')}</div>`;
```

### 4. Placeholder Replacement

For messages with dynamic values:

```javascript
// In i18n.js:
discoveredDevices: 'Discovered {count} devices, added {added} new'

// In code:
i18n.t('discoveredDevices')
    .replace('{count}', data.discovered_count)
    .replace('{added}', data.added_count)
```

## Translation Key Categories

| Category | Examples |
|----------|----------|
| Navigation | `topology`, `devices`, `alerts`, `groups`, `settings` |
| Common Actions | `save`, `cancel`, `delete`, `edit`, `add`, `close` |
| Alert Details | `device`, `message`, `timeline`, `status`, `triggeredAt` |
| Settings | `snmpTestingTools`, `targetIp`, `communityString` |
| Dynamic Messages | `testing`, `discovering`, `discoveryComplete` |

## Adding New Translations

When adding new translatable text:

1. Add the key to **all three language sections** in `i18n.js`
2. Use meaningful, camelCase key names
3. For HTML: Add `data-i18n="keyName"` attribute
4. For JS: Use `i18n.t('keyName')`

### Example

```javascript
// 1. Add to i18n.js (all three languages)
// English:
myNewKey: 'My New Text',

// zh-TW:
myNewKey: '我的新文字',

// zh-CN:
myNewKey: '我的新文字',

// 2. Use in HTML:
<span data-i18n="myNewKey">My New Text</span>

// 3. Or use in JavaScript:
element.textContent = i18n.t('myNewKey');
```

## Language Switching

Language preference is stored in `localStorage` under the key `language`. The system:

1. Checks for saved preference on page load
2. Defaults to English if no preference exists
3. Updates all elements with `data-i18n` attributes when language changes

## Files Modified for i18n

### Recent Updates (2025-12-13)

| File | Changes |
|------|---------|
| `static/js/i18n.js` | Added ~30 new translation keys for settings and alerts |
| `static/settings.html` | Converted 16+ hardcoded Chinese labels to use `data-i18n` |
| `static/alerts.html` | Fixed detail modal labels (device, message, timeline, etc.) |
| `static/devices.html` | Added `data-i18n` to navigation menu |

### Key Additions

- SNMP Testing: `snmpConnectionTest`, `testResult`, `testing`
- Discovery: `manualDiscovery`, `startDiscovery`, `discovering`, `discoveryComplete`
- Subnet Restriction: `cidrHelpText`, `subnetRestrictionHelp`
- OID Options: `sysDescr`, `sysName`, `sysUpTime`, `lldpNeighbors`
- Dynamic Messages: `enterTargetIp`, `discoveredDevices`, `settingsSaved`
