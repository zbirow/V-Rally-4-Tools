# V-Rally 4 (.PKG) - File Format Specification

## 1. Global Header
Located at the beginning of the file (`0x00`).

| Offset (Hex) | Type | Name | Description |
| :--- | :--- | :--- | :--- |
| `0x00` | char[4] | **Magic** | Always `PPKG` (`0x474B5050`) |
| `0x04` | uint32 | **Version** | File format version (e.g., `1` or `2`) |
| `0x08` | uint32 | **File Count** | Total number of files contained in the archive |
| `0x0C` | uint32 | **Index Info** | Likely Index size |
| `0x10` | byte[32] | **Padding** | Reserved space, usually zeros |

**Total Header Size:** 48 bytes.

---

## 2. File Index (Table of Contents)
Immediately follows the header (starts at `0x30`). The index is a sequential list of entries. Each entry consists of a **Variable Length Name** followed by a **Fixed Length Metadata Block**.

### Entry Structure

#### Part A: Filename
| Type | Description |
| :--- | :--- |
| `uint32` | **Name Length** (N) |
| `char[N]` | **File Path** (String, NOT null-terminated in length count, but may contain null byte) |

*Note:* The file path usually includes internal directory structures (e.g., `WIN32\GRAPH\TEXTURES\...`).

#### Part B: Metadata Block (Fixed 80 bytes)
Immediately follows the name string.

| Offset (Relative) | Type | Name | Description |
| :--- | :--- | :--- | :--- |
| `0x00` | uint32 | Unknown | Skip (Flags?) |
| `0x04` | uint32 | **Data Offset** | Absolute offset to the file data start |
| `0x08` | byte[12] | Unknown | Padding / Unknown data |
| `0x14` | uint32 | **Data Size** | Total size of the data chunk (includes `PKGB` header) |
| `0x18` | byte[56] | Padding | Remaining reserved space to complete the 80-byte block |

---

## 3. Data Storage
Files are stored at the `Data Offset` retrieved from the Metadata Block.

### Data Chunk Structure
Each file data block is wrapped in custom headers.

| Offset (Relative) | Type | Value | Description |
| :--- | :--- | :--- | :--- |
| `0x00` | char[4] | **PKGB** | **Start Magic**. Indicates beginning of data. |
| `0x04` | byte[...] | **Payload** | The actual file content (Texture, Model, etc.) |
| `End` | char[4] | **PKGE** | **End Magic**. Indicates end of data block. |

### Extraction Logic
To correctly extract the raw file:
1. Go to `Data Offset`.
2. Verify the first 4 bytes are `PKGB`.
3. **Skip** these 4 bytes.
4. Read `Data Size - 4` bytes.
   * *Note:* The `Data Size` in the index includes the 4-byte `PKGB` header.

---

## 4. Known Directory Structures
Paths inside the archive use backslashes (`\`) as separators.
Examples:
- `WIN32\GRAPH\TEXTURES\SKY\...`
- `WIN32\VEHICLES\...`
- 
When extracting, these paths should be converted to the host OS format (e.g., `/` for Linux/macOS) and directories should be created recursively.


## 5. Unpack

usage: `python ppkg_unpack_gui.py`
