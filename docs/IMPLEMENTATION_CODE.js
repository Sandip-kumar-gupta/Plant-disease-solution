// DISEASE DETECTION ENGINE - Complete Implementation
// Copy and use this code in your project

class DiseaseDetectionEngine {
  constructor(diseaseDatabase) {
    this.diseases = diseaseDatabase;
  }

  // Get disease by ID
  getDiseaseInfo(diseaseId) {
    return this.diseases[diseaseId] || null;
  }

  // Handle symptom submission
  async handleSymptomSubmit(symptoms) {
    // symptoms = ["fever", "cough", "fatigue"]
    try {
      // Call your ML model
      const prediction = await this.predictDisease(symptoms);
      
      if (prediction) {
        const diseaseInfo = this.getDiseaseInfo(prediction.diseaseId);
        return {
          success: true,
          disease: diseaseInfo,
          confidence: prediction.confidence,
          timestamp: new Date()
        };
      }
    } catch (error) {
      console.error('Error in symptom detection:', error);
      return { success: false, error: error.message };
    }
  }

  // Predict disease (call your ML model)
  async predictDisease(symptoms) {
    // Replace with your actual ML model call
    // Example: POST to /api/predict with symptoms
    const response = await fetch('/api/ml-model/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symptoms: symptoms })
    });
    
    const result = await response.json();
    return result; // {diseaseId: "covid19", confidence: 0.87}
  }

  // Get all disease info for display
  displayDiseaseResult(disease, confidence) {
    return {
      name: disease.name,
      confidence: (confidence * 100).toFixed(1) + '%',
      causes: disease.causes,
      prevention: disease.prevention,
      treatment: disease.treatment,
      medications: disease.medications,
      emergency: disease.emergency,
      prognosis: disease.prognosis
    };
  }

  // Set medication reminder
  setMedicationReminder(medicationName, time, userId) {
    const reminder = {
      medicationName: medicationName,
      time: time,
      userId: userId,
      enabled: true,
      createdAt: new Date()
    };

    // Save to database
    fetch('/api/reminders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reminder)
    });

    // Request notification permission
    if ('Notification' in window) {
      Notification.requestPermission();
    }

    return reminder;
  }

  // Save detection result to history
  saveToDiseaseHistory(diseaseId, confidence, symptoms) {
    const record = {
      disease: diseaseId,
      confidence: confidence,
      symptoms: symptoms,
      date: new Date(),
      status: 'ongoing'
    };

    // Save to localStorage or database
    let history = JSON.parse(localStorage.getItem('diseaseHistory') || '[]');
    history.push(record);
    localStorage.setItem('diseaseHistory', JSON.stringify(history));

    return record;
  }

  // Get disease history
  getDiseaseHistory() {
    return JSON.parse(localStorage.getItem('diseaseHistory') || '[]');
  }

  // Calculate progress based on days and success metrics
  calculateProgress(disease, dayNumber) {
    if (!disease.success_metrics) return 0;

    if (dayNumber <= 7) {
      // Week 1: expected improvement
      return Math.min((dayNumber / 7) * 30, 30);
    } else if (dayNumber <= 30) {
      // 30 days: expected recovery
      return Math.min(30 + ((dayNumber - 7) / 23) * 40, 70);
    } else {
      // Beyond 30 days: full recovery trajectory
      return Math.min(70 + ((dayNumber - 30) / 60) * 30, 100);
    }
  }

  // Format disease info for display
  formatDiseaseInfo(disease) {
    return `
      <div class="disease-result">
        <h2>${disease.name}</h2>
        
        <div class="section">
          <h3>Root Causes</h3>
          <p>${disease.causes}</p>
        </div>
        
        <div class="section">
          <h3>Prevention</h3>
          <p>${disease.prevention}</p>
        </div>
        
        <div class="section">
          <h3>Treatment Plan</h3>
          ${disease.treatment.stages.map(stage => `
            <div class="treatment-stage">
              <h4>${stage.name}</h4>
              <p>${stage.description}</p>
              <ul>
                ${stage.components.map(c => `<li>${c}</li>`).join('')}
              </ul>
            </div>
          `).join('')}
        </div>
        
        <div class="section">
          <h3>Medications</h3>
          ${disease.medications.map(med => `
            <div class="medication-card">
              <h4>${med.name}</h4>
              <p>Dosage: ${med.dosage}</p>
              <p>Frequency: ${med.frequency}</p>
              <p>Side Effects: ${med.side_effects.join(', ')}</p>
              <button onclick="setReminder('${med.name}')">Set Reminder</button>
            </div>
          `).join('')}
        </div>
        
        <div class="section emergency">
          <h3>⚠️ Emergency Signs</h3>
          <ul>
            ${disease.emergency.signs.map(sign => `<li>${sign}</li>`).join('')}
          </ul>
          <p><strong>${disease.emergency.action}</strong></p>
        </div>
      </div>
    `;
  }
}

// HTML Form Handler
function initSymptomChecker() {
  const form = document.getElementById('symptom-form');
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get selected symptoms
    const checkboxes = document.querySelectorAll('input[name="symptoms"]:checked');
    const symptoms = Array.from(checkboxes).map(cb => cb.value);
    
    if (symptoms.length === 0) {
      alert('Please select at least one symptom');
      return;
    }
    
    // Show loading
    document.getElementById('result').innerHTML = '<p>Detecting disease...</p>';
    
    // Get prediction from ML model
    try {
      const response = await fetch('/api/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms: symptoms })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Display disease info
        const engine = new DiseaseDetectionEngine(window.DISEASE_DATABASE);
        const formatted = engine.formatDiseaseInfo(result.disease);
        document.getElementById('result').innerHTML = formatted;
        
        // Save to history
        engine.saveToDiseaseHistory(result.disease.id, result.confidence, symptoms);
      } else {
        document.getElementById('result').innerHTML = '<p>Unable to detect disease. Please try again.</p>';
      }
    } catch (error) {
      console.error('Error:', error);
      document.getElementById('result').innerHTML = '<p>Error processing request.</p>';
    }
  });
}

// Set medication reminder
function setReminder(medicationName) {
  const time = prompt(`Set time for ${medicationName} reminder (e.g., 08:00):`);
  if (time) {
    const engine = new DiseaseDetectionEngine(window.DISEASE_DATABASE);
    const reminder = engine.setMedicationReminder(medicationName, time, getCurrentUserId());
    alert(`Reminder set for ${medicationName} at ${time}`);
  }
}

// Export to PDF
function exportToPDF(disease, confidence) {
  // Requires jsPDF library
  const doc = new jsPDF();
  
  // Add title
  doc.setFontSize(20);
  doc.text(disease.name, 10, 10);
  
  // Add confidence
  doc.setFontSize(12);
  doc.text(`Confidence: ${(confidence * 100).toFixed(1)}%`, 10, 25);
  doc.text(`Date: ${new Date().toLocaleDateString()}`, 10, 35);
  
  // Add disease info
  let yPosition = 45;
  doc.setFontSize(14);
  
  doc.text('Medical Information', 10, yPosition);
  yPosition += 10;
  
  doc.setFontSize(11);
  doc.text('Causes:', 10, yPosition);
  yPosition += 5;
  
  const causesLines = doc.splitTextToSize(disease.causes, 180);
  doc.text(causesLines, 10, yPosition);
  yPosition += causesLines.length * 5 + 5;
  
  // Add more sections...
  doc.text('Treatment and Medications:', 10, yPosition);
  yPosition += 10;
  
  // Save PDF
  doc.save(`${disease.name}-Report.pdf`);
}

// Dashboard/Progress tracking
function initDashboard(disease, startDate) {
  const today = new Date();
  const daysPassed = Math.floor((today - startDate) / (1000 * 60 * 60 * 24));
  
  const engine = new DiseaseDetectionEngine(window.DISEASE_DATABASE);
  const progressPercent = engine.calculateProgress(disease, daysPassed);
  
  // Create chart
  const ctx = document.getElementById('progress-chart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Day 1', 'Day 3', 'Day 7', 'Day 14', 'Day 30'],
      datasets: [{
        label: 'Recovery Progress %',
        data: [
          engine.calculateProgress(disease, 1),
          engine.calculateProgress(disease, 3),
          engine.calculateProgress(disease, 7),
          engine.calculateProgress(disease, 14),
          engine.calculateProgress(disease, 30)
        ],
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      }
    }
  });
  
  // Update progress display
  document.getElementById('progress-percent').textContent = Math.round(progressPercent) + '%';
  document.getElementById('days-passed').textContent = daysPassed;
}

// Get current user ID (implement based on your auth)
function getCurrentUserId() {
  return localStorage.getItem('userId') || 'anonymous';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initSymptomChecker();
  // Initialize other components as needed
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DiseaseDetectionEngine;
}