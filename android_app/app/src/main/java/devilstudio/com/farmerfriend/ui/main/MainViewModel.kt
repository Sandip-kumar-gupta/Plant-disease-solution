package devilstudio.com.farmerfriend.ui.main

import android.graphics.Bitmap
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import devilstudio.com.farmerfriend.data.model.DiseaseResult
import devilstudio.com.farmerfriend.ml.PlantDiseaseClassifier
import kotlinx.coroutines.launch
import timber.log.Timber
import javax.inject.Inject

@HiltViewModel
class MainViewModel @Inject constructor(
    private val classifier: PlantDiseaseClassifier
) : ViewModel() {
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _classificationResult = MutableLiveData<DiseaseResult?>()
    val classificationResult: LiveData<DiseaseResult?> = _classificationResult
    
    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error
    
    private val _isInitialized = MutableLiveData<Boolean>()
    val isInitialized: LiveData<Boolean> = _isInitialized
    
    init {
        initializeClassifier()
    }
    
    private fun initializeClassifier() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val success = classifier.initialize()
                _isInitialized.value = success
                if (!success) {
                    _error.value = "Failed to initialize AI model. Please restart the app."
                }
                Timber.d("Classifier initialization: $success")
            } catch (e: Exception) {
                Timber.e(e, "Error initializing classifier")
                _error.value = "Error initializing AI model: ${e.message}"
                _isInitialized.value = false
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    fun classifyImage(bitmap: Bitmap) {
        if (!classifier.isInitialized()) {
            _error.value = "AI model not ready. Please wait for initialization to complete."
            return
        }
        
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            
            try {
                val result = classifier.classifyImage(bitmap)
                _classificationResult.value = result
                
                if (result == null) {
                    _error.value = "Could not classify the image. Please try with a clearer image of a plant leaf."
                }
            } catch (e: Exception) {
                Timber.e(e, "Error during classification")
                _error.value = "Classification failed: ${e.message}"
                _classificationResult.value = null
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    fun clearResult() {
        _classificationResult.value = null
        _error.value = null
    }
    
    fun clearError() {
        _error.value = null
    }
    
    override fun onCleared() {
        super.onCleared()
        classifier.cleanup()
    }
}