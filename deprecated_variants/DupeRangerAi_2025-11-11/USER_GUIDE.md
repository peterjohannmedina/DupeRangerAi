# DupeRangerAi - Smart File Organizer

## 🏠 Welcome to DupeRangerAi

**Tired of messy files and duplicate clutter?** DupeRangerAi is your intelligent file organization assistant that automatically finds, categorizes, and organizes your digital files with the help of AI.

**Version 1.1** | **Free & Open Source** | **Windows Compatible**

---

## ✨ What Makes DupeRangerAi Special?

### 🔍 **Smart Duplicate Detection**
- **Lightning Fast**: Uses advanced algorithms to scan thousands of files in seconds
- **100% Accurate**: Combines quick scanning with thorough verification to find true duplicates
- **Flexible Choices**: Decide whether to keep the oldest or newest version of duplicate files
- **Safe Handling**: Automatically marks duplicates instead of deleting them

### 🤖 **AI-Powered Organization**
- **Intelligent Categories**: Automatically sorts files into logical groups like Photos, Documents, Videos, Music, and more
- **Learns File Types**: Uses AI to understand what each file is, not just its extension
- **Works on Any Language**: Recognizes files regardless of your computer's language settings
- **Gets Smarter**: Improves categorization as you use it

### 🛡️ **Built for Safety**
- **Preview Before Action**: See exactly what will happen before any files are moved
- **Test Mode**: Try organization without making permanent changes
- **Detailed Logs**: Keep track of all changes for easy reversal if needed
- **No Data Loss**: Never deletes files without your explicit approval

---

## 🚀 Quick Start Guide

### What You Need
- **Windows 10 or 11** (64-bit recommended)
- **About 100MB free space** for the program
- **Internet connection** (only needed for AI features during first use)

### Step 1: Get the Software
```bash
# Download from GitHub
git clone https://github.com/yourusername/duperangerai.git
cd duperangerai
```

### Step 2: Install Dependencies
```powershell
# Easy one-command setup
.\install_deps.ps1
```

### Step 3: Launch the App
```powershell
python DupeRangerAi.py
```

**That's it!** The app opens in a clean, easy-to-use window.

---

## 📖 How to Use DupeRangerAi

### Basic File Organization

1. **Choose Your Folder**: Click "Browse" and select the folder you want to organize
2. **Pick Your Options**:
   - Check "Compute SHA-256 hashes" to find duplicates
   - Check "Enable AI categorization" for smart organization
3. **Start Scanning**: Click the "Scan" button and watch the progress
4. **Review Results**: Check the three tabs to see your files organized by type, duplicates found, and AI categories
5. **Apply Changes**: Click "Apply Actions" to organize your files

### Understanding the Results

- **By Extension**: Shows all file types and how much space they use
- **Duplicates**: Lists files that are exactly the same (with different names)
- **AI Categories**: Shows how the AI grouped your files (Photos, Documents, etc.)

### Advanced Features

- **Performance Tuning**: Adjust scan speed based on your storage type (fast SSD vs. slower network drives)
- **Worker Count**: Let the app automatically use the right number of CPU cores for your computer
- **Dry Run Mode**: Test organization without making real changes

---

## 🔒 Privacy & Security

### Your Files Stay Private
- **Local Processing**: All scanning and AI analysis happens on your computer
- **No Uploads**: Your files never leave your machine
- **No Internet Required**: Works offline once AI models are downloaded
- **No Data Collection**: We don't track or collect any information about your files

### Safe File Handling
- **Read-Only by Default**: The app only reads your files to analyze them
- **Permission-Based**: Respects your file permissions and access rights
- **Error Recovery**: Handles locked files gracefully without crashing
- **Undo Capability**: Detailed logs help you reverse any changes if needed

---

## 🛠️ Performance Tips

### For Fast Storage (SSD/NVMe)
- Use default settings - optimized for speed
- Great for organizing large photo or video collections

### For Network Drives
- Reduce chunk sizes in advanced settings
- Lower worker count to avoid network congestion
- Perfect for organizing files on NAS or cloud storage

### For AI Features
- First scan with AI may take longer while models download
- Subsequent scans are much faster
- AI works on CPU if you don't have a dedicated graphics card

---

## 🤝 About the Developer

**DupeRangerAi** was created by **Peter Johann Medina**, an independent developer passionate about making technology more accessible and useful.

**Learn more about Peter's work**: [https://ReclaimDev.com](https://ReclaimDev.com)

Peter develops practical software solutions that help people manage their digital lives more effectively. DupeRangerAi represents a commitment to creating powerful yet user-friendly tools that anyone can use.

---

## 📄 License & Legal

### Free & Open Source
DupeRangerAi is **completely free** to use, modify, and distribute. It's released under the **MIT License**, which means:

- ✅ **No cost** to download or use
- ✅ **No restrictions** on personal or commercial use
- ✅ **Freedom to modify** and improve the software
- ✅ **Permission to distribute** copies to others

### What This Means for You
- **No hidden fees** or subscriptions
- **No licensing restrictions** for business use
- **Community supported** - improvements come from users like you
- **Transparent development** - all code is openly available

### Important Legal Notes
- **As-Is Software**: Provided without any warranties or guarantees
- **Use at Your Own Risk**: While designed to be safe, file operations carry inherent risks
- **Backup First**: Always backup important files before organizing
- **Test Thoroughly**: Use dry-run mode to verify changes before applying

---

## 🆘 Getting Help

### Common Questions

**"The AI features don't work"**
- Run `.\install_deps.ps1 -UseGPU` to install AI components
- Check that you have internet for the first AI model download

**"Scanning is slow"**
- Reduce worker count in advanced settings
- Check antivirus exclusions for the scan folder
- Use smaller chunk sizes for network storage

**"Permission errors"**
- Try running as Administrator
- Check file/folder permissions
- Some system files may be protected

### Support Options
- **Documentation**: Check the detailed README.md for technical details
- **Community**: Open issues on GitHub for bugs or feature requests
- **Developer**: Contact through ReclaimDev.com for custom development

---

## 🎉 Why Choose DupeRangerAi?

### Compared to Other Organizers
- **Smarter**: Uses AI to understand file content, not just names
- **Safer**: Preview and test modes prevent accidental changes
- **Faster**: Optimized algorithms handle large file collections quickly
- **Free**: No cost, no subscriptions, no limitations

### Perfect For
- 📸 **Photo Collections**: Automatically organize thousands of images
- 📁 **Document Management**: Sort work files by type and project
- 🎵 **Media Libraries**: Keep music, videos, and podcasts organized
- 💼 **Business Use**: Clean up shared drives and network storage
- 🏠 **Home Organization**: Tame digital clutter across multiple devices

### Real User Benefits
- **Save Time**: Automate hours of manual file sorting
- **Free Up Space**: Identify and remove true duplicates
- **Better Organization**: Find files faster with logical categories
- **Peace of Mind**: Safe operations with full control and logging

---

## 🚀 What's Next?

DupeRangerAi continues to evolve with new features and improvements. Future updates may include:

- **Cloud Storage Support**: Direct integration with cloud drives
- **Advanced AI Models**: Even smarter file categorization
- **Batch Processing**: Handle multiple folders simultaneously
- **Mobile Companion**: Organize files on phones and tablets

**Have ideas for new features?** Open a GitHub issue or visit ReclaimDev.com to share your suggestions!

---

**Ready to get organized?** Download DupeRangerAi today and take control of your digital files!

*Developed with ❤️ by Peter Johann Medina* | *Free & Open Source Forever*