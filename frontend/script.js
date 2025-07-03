class VoiceAssistant {
  constructor() {
    this.micBtn = document.getElementById("mic-btn");
    this.micIcon = document.getElementById("mic-icon");
    this.modeSelect = document.getElementById("mode-select");
    this.questionBox = document.getElementById("question-box");
    this.placeholder = document.getElementById("placeholder");
    this.transcriptionText = document.getElementById("transcription-text");
    this.statusText = document.getElementById("status-text");
    this.answerBox = document.getElementById("answer-box");
    
    // Document upload elements
    this.documentSection = document.getElementById("document-section");
    this.uploadArea = document.getElementById("upload-area");
    this.fileInput = document.getElementById("file-input");
    this.filesList = document.getElementById("files-list");
    this.filesContainer = document.getElementById("files-container");
    
    this.isListening = false;
    this.uploadedFiles = [];
    
    this.init();
  }

  init() {
    this.micBtn.addEventListener("click", () => this.handleMicClick());
    this.modeSelect.addEventListener("change", () => this.handleModeChange());
    this.setupDocumentUpload();
    this.addKeyboardSupport();
    this.addAnimations();
    
    // Initialize mode
    this.handleModeChange();
  }

  handleModeChange() {
    const mode = this.modeSelect.value;
    
    if (mode === 'document') {
      this.documentSection.classList.remove('hidden');
      this.documentSection.style.animation = 'slide-up 0.5s ease-out';
    } else {
      this.documentSection.classList.add('hidden');
    }
  }

  setupDocumentUpload() {
    // File input change
    this.fileInput.addEventListener('change', (e) => {
      this.handleFiles(e.target.files);
    });

    // Drag and drop
    this.uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      this.uploadArea.classList.add('dragover');
    });

    this.uploadArea.addEventListener('dragleave', (e) => {
      e.preventDefault();
      this.uploadArea.classList.remove('dragover');
    });

    this.uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      this.uploadArea.classList.remove('dragover');
      this.handleFiles(e.dataTransfer.files);
    });

    // Click to upload
    this.uploadArea.addEventListener('click', () => {
      this.fileInput.click();
    });
  }

  handleFiles(files) {
    const validTypes = ['.pdf', '.doc', '.docx', '.txt'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    Array.from(files).forEach(file => {
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      
      if (!validTypes.includes(fileExtension)) {
        this.showNotification(`File type not supported: ${file.name}`, 'error');
        return;
      }

      if (file.size > maxSize) {
        this.showNotification(`File too large: ${file.name}`, 'error');
        return;
      }

      // Check if file already exists
      if (this.uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
        this.showNotification(`File already uploaded: ${file.name}`, 'warning');
        return;
      }

      this.uploadedFiles.push(file);
      this.addFileToList(file);
      this.showNotification(`File uploaded: ${file.name}`, 'success');
    });

    if (this.uploadedFiles.length > 0) {
      this.filesList.classList.remove('hidden');
    }

    // Clear input
    this.fileInput.value = '';
  }

  addFileToList(file) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.style.animation = 'slide-up 0.3s ease-out';

    const fileSize = this.formatFileSize(file.size);
    const fileIcon = this.getFileIcon(file.name);

    fileItem.innerHTML = `
      <div class="file-info">
        <svg class="file-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          ${fileIcon}
        </svg>
        <div class="file-details">
          <div class="file-name">${file.name}</div>
          <div class="file-size">${fileSize}</div>
        </div>
      </div>
      <button class="file-remove" onclick="voiceAssistant.removeFile('${file.name}', ${file.size})" aria-label="Remove file">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    `;

    this.filesContainer.appendChild(fileItem);
  }

  removeFile(fileName, fileSize) {
    this.uploadedFiles = this.uploadedFiles.filter(f => !(f.name === fileName && f.size === fileSize));
    
    // Remove from DOM
    const fileItems = this.filesContainer.querySelectorAll('.file-item');
    fileItems.forEach(item => {
      const nameElement = item.querySelector('.file-name');
      if (nameElement && nameElement.textContent === fileName) {
        item.style.animation = 'fade-out 0.3s ease-out';
        setTimeout(() => item.remove(), 300);
      }
    });

    if (this.uploadedFiles.length === 0) {
      this.filesList.classList.add('hidden');
    }

    this.showNotification(`File removed: ${fileName}`, 'success');
  }

  getFileIcon(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    
    switch (extension) {
      case 'pdf':
        return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>';
      case 'doc':
      case 'docx':
        return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>';
      case 'txt':
        return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>';
      default:
        return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>';
    }
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${type === 'success' ? 'rgba(16, 185, 129, 0.9)' : 
                   type === 'error' ? 'rgba(239, 68, 68, 0.9)' : 
                   type === 'warning' ? 'rgba(245, 158, 11, 0.9)' : 
                   'rgba(59, 130, 246, 0.9)'};
      color: white;
      padding: 12px 20px;
      border-radius: 12px;
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
      z-index: 1000;
      font-size: 14px;
      font-weight: 500;
      max-width: 300px;
      animation: slide-in-right 0.3s ease-out;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);

    // Auto remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = 'slide-out-right 0.3s ease-out';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  addKeyboardSupport() {
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault();
        this.micBtn.click();
      }
    });
  }

  addAnimations() {
    // Add entrance animation
    const mainCard = document.querySelector('.main-card');
    mainCard.style.opacity = '0';
    mainCard.style.transform = 'translateY(30px)';
    
    setTimeout(() => {
      mainCard.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
      mainCard.style.opacity = '1';
      mainCard.style.transform = 'translateY(0)';
    }, 200);

    // Add CSS for notifications
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slide-in-right {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
      
      @keyframes slide-out-right {
        from {
          transform: translateX(0);
          opacity: 1;
        }
        to {
          transform: translateX(100%);
          opacity: 0;
        }
      }
      
      @keyframes fade-out {
        from {
          opacity: 1;
          transform: translateY(0);
        }
        to {
          opacity: 0;
          transform: translateY(-10px);
        }
      }
    `;
    document.head.appendChild(style);
  }

  async handleMicClick() {
    if (this.isListening) return;
    
    try {
      this.startListening();
      const mode = this.modeSelect.value;
      
      // Show listening state
      this.showListeningState();
      
      // Prepare request data
      const requestData = {
        mode: mode,
        files: mode === 'document' ? this.uploadedFiles.map(f => ({
          name: f.name,
          size: f.size,
          type: f.type
        })) : []
      };
      
      // Make API call
      const response = await fetch("http://127.0.0.1:8000/transcribe", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Update UI with transcription
      this.showTranscription(data.question);
      
    } catch (error) {
      console.error("Error:", error);
      this.showError("Could not connect to the transcription service. Please make sure the server is running.");
    } finally {
      this.stopListening();
    }
  }

  startListening() {
    this.isListening = true;
    this.micBtn.classList.add("listening");
    this.statusText.textContent = "Listening...";
    this.statusText.style.color = '#10b981';
    
    // Change icon to listening state
    this.micIcon.innerHTML = `
      <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
      <path fill-rule="evenodd" d="M4 5a2 2 0 012-2h8a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm2 0v6h8V5H6z" clip-rule="evenodd"></path>
    `;
  }

  stopListening() {
    this.isListening = false;
    this.micBtn.classList.remove("listening");
    this.statusText.textContent = "Tap to speak";
    this.statusText.style.color = '';
    
    // Reset icon to microphone
    this.micIcon.innerHTML = `
      <path fill-rule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clip-rule="evenodd"></path>
    `;
  }

  showListeningState() {
    this.placeholder.classList.add('hidden');
    this.transcriptionText.classList.remove('hidden');
    this.transcriptionText.innerHTML = `
      <div class="flex items-center justify-center">
        <div class="animate-spin w-5 h-5 border-2 border-white/30 border-t-white rounded-full mr-3"></div>
        <span style="color: rgba(79, 172, 254, 0.9);">Listening and transcribing...</span>
      </div>
    `;
    
    // Add listening effect to the transcription area
    this.questionBox.classList.add('listening-state');
  }

  showTranscription(text) {
    this.placeholder.classList.add('hidden');
    this.transcriptionText.classList.remove('hidden');
    this.transcriptionText.innerHTML = `
      <div style="animation: fade-in 0.5s ease-out;">
        <div class="flex items-start mb-3">
          <svg class="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" style="color: #10b981;" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span style="color: rgba(16, 185, 129, 0.9); font-size: 0.875rem; font-weight: 600;">Transcribed Successfully</span>
        </div>
        <p style="color: rgba(255, 255, 255, 0.95); font-size: 1.125rem; line-height: 1.6; font-weight: 400;">${text}</p>
      </div>
    `;
    
    // Reset transcription area styling
    this.questionBox.classList.remove('listening-state');
    this.questionBox.classList.add('success-state');
    
    // Show success state briefly
    this.statusText.textContent = "Transcription complete";
    this.statusText.style.color = '#10b981';
    
    setTimeout(() => {
      this.statusText.textContent = "Tap to speak";
      this.statusText.style.color = '';
      this.questionBox.classList.remove('success-state');
    }, 2500);
  }

  showError(message) {
    this.placeholder.classList.add('hidden');
    this.transcriptionText.classList.remove('hidden');
    this.transcriptionText.innerHTML = `
      <div style="animation: fade-in 0.5s ease-out;">
        <div class="flex items-start mb-3">
          <svg class="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" style="color: #ef4444;" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
          </svg>
          <span style="color: rgba(239, 68, 68, 0.9); font-size: 0.875rem; font-weight: 600;">Connection Error</span>
        </div>
        <p style="color: rgba(255, 255, 255, 0.9); font-size: 1rem; line-height: 1.5;">${message}</p>
      </div>
    `;
    
    // Style transcription area for error
    this.questionBox.classList.remove('listening-state');
    this.questionBox.classList.add('error-state');
    
    // Show error state
    this.statusText.textContent = "Connection failed";
    this.statusText.style.color = '#ef4444';
    
    setTimeout(() => {
      this.statusText.textContent = "Tap to speak";
      this.statusText.style.color = '';
      this.questionBox.classList.remove('error-state');
    }, 4000);
  }
}

// Initialize the voice assistant when DOM is loaded
let voiceAssistant;
document.addEventListener('DOMContentLoaded', () => {
  voiceAssistant = new VoiceAssistant();
});