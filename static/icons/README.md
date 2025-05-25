# File Icons

This directory contains icons for different file types displayed in the application.

## Current Icons
- ✅ `default.png` - Default file icon
- ✅ `excel.png` - Excel spreadsheets (.xlsx, .xls)
- ✅ `image.png` - Image files (.png, .jpg, .jpeg, .gif)
- ✅ `pdf.png` - PDF documents
- ✅ `word.png` - Word documents (.docx, .doc)

## Missing Icons (Need to be added)
- ❌ `powerpoint.png` - PowerPoint presentations (.pptx, .ppt)
- ❌ `panda.png` - Panda archive files (.panda)

## Icon Requirements
- **Size**: 64x64 pixels (or similar square format)
- **Format**: PNG with transparent background
- **Style**: Modern, minimal, flat design (consistent with existing icons)
- **Colors**: 
  - PowerPoint: `#D24726` (PowerPoint orange-red)
  - Panda: `#FFA726` (Amber/golden yellow) or custom panda-themed colors

## MIME Type Support
The application supports both MIME types and file extensions for icon detection:

### PowerPoint
- MIME: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- MIME: `application/vnd.ms-powerpoint`
- Extensions: `.pptx`, `.ppt`

### Panda Files
- Extensions: `.panda` (treated as ZIP archives)

## Adding New Icons
1. Add the icon file to this directory
2. Update `fileIcons` object in `/static/script.js` for MIME type support
3. Update `extensionIcons` object in `/static/script.js` for extension support