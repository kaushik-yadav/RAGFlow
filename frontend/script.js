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
    
    this.isListening = false;
    this.init();
  }

  init() {
    this.micBtn.addEventListener("click", () => this.handleMicClick());
    this.addKeyboardSupport();
    this.addAnimations();
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
    const mainCard = document.querySelector('.glass-card');
    mainCard.style.opacity = '0';
    mainCard.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
      mainCard.style.transition = 'all 0.6s ease-out';
      mainCard.style.opacity = '1';
      mainCard.style.transform = 'translateY(0)';
    }, 100);
  }

  async handleMicClick() {
    if (this.isListening) return;
    
    try {
      this.startListening();
      const mode = this.modeSelect.value;
      
      // Show listening state
      this.showListeningState();
      
      // Make API call
      const response = await fetch("http://127.0.0.1:8000/transcribe");
      
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
    
    // Change icon to stop/listening icon
    this.micIcon.innerHTML = `
      <path fill-rule="evenodd" d="M18 8a1 1 0 01-1 1h-1.5A4.5 4.5 0 0111 13.5V15h2a1 1 0 110 2H7a1 1 0 110-2h2v-1.5A4.5 4.5 0 014.5 9H3a1 1 0 01-1-1V6a1 1 0 011-1h1.5A4.5 4.5 0 019 .5h2A4.5 4.5 0 0115.5 5H17a1 1 0 011 1v2z" clip-rule="evenodd"></path>
    `;
  }

  stopListening() {
    this.isListening = false;
    this.micBtn.classList.remove("listening");
    this.statusText.textContent = "Tap to speak";
    
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
        <span class="text-blue-200">Listening and transcribing...</span>
      </div>
    `;
    
    // Add pulsing effect to the transcription area
    this.questionBox.style.background = 'rgba(59, 130, 246, 0.2)';
    this.questionBox.style.borderColor = 'rgba(59, 130, 246, 0.4)';
  }

  showTranscription(text) {
    this.placeholder.classList.add('hidden');
    this.transcriptionText.classList.remove('hidden');
    this.transcriptionText.innerHTML = `
      <div class="animate-fade-in">
        <div class="flex items-start mb-2">
          <svg class="w-5 h-5 text-green-400 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span class="text-green-200 text-sm font-medium">Transcribed</span>
        </div>
        <p class="text-white text-lg leading-relaxed">${text}</p>
      </div>
    `;
    
    // Reset transcription area styling
    this.questionBox.style.background = 'rgba(255, 255, 255, 0.1)';
    this.questionBox.style.borderColor = 'rgba(255, 255, 255, 0.2)';
    
    // Show success state briefly
    this.statusText.textContent = "Transcription complete";
    this.statusText.style.color = '#10b981';
    
    setTimeout(() => {
      this.statusText.textContent = "Tap to speak";
      this.statusText.style.color = '';
    }, 2000);
  }

  showError(message) {
    this.placeholder.classList.add('hidden');
    this.transcriptionText.classList.remove('hidden');
    this.transcriptionText.innerHTML = `
      <div class="animate-fade-in">
        <div class="flex items-start mb-2">
          <svg class="w-5 h-5 text-red-400 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
          </svg>
          <span class="text-red-200 text-sm font-medium">Error</span>
        </div>
        <p class="text-red-100 text-base leading-relaxed">${message}</p>
      </div>
    `;
    
    // Style transcription area for error
    this.questionBox.style.background = 'rgba(239, 68, 68, 0.2)';
    this.questionBox.style.borderColor = 'rgba(239, 68, 68, 0.4)';
    
    // Show error state
    this.statusText.textContent = "Connection failed";
    this.statusText.style.color = '#ef4444';
    
    setTimeout(() => {
      this.statusText.textContent = "Tap to speak";
      this.statusText.style.color = '';
      this.questionBox.style.background = 'rgba(255, 255, 255, 0.1)';
      this.questionBox.style.borderColor = 'rgba(255, 255, 255, 0.2)';
    }, 3000);
  }
}

// Initialize the voice assistant when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new VoiceAssistant();
});