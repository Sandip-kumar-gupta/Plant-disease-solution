package devilstudio.com.farmerfriend

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import dagger.hilt.android.AndroidEntryPoint
import devilstudio.com.farmerfriend.databinding.ActivityMainBinding
import devilstudio.com.farmerfriend.ui.main.MainViewModel
import timber.log.Timber
import java.io.IOException

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    private val viewModel: MainViewModel by viewModels()
    
    private var currentBitmap: Bitmap? = null
    
    // Activity result launchers
    private val cameraLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val imageBitmap = result.data?.extras?.get("data") as? Bitmap
            imageBitmap?.let { handleImageResult(it) }
        }
    }
    
    private val galleryLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                try {
                    val bitmap = MediaStore.Images.Media.getBitmap(contentResolver, uri)
                    handleImageResult(bitmap)
                } catch (e: IOException) {
                    Timber.e(e, "Error loading image from gallery")
                    showError("Failed to load image from gallery")
                }
            }
        }
    }
    
    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val cameraGranted = permissions[Manifest.permission.CAMERA] ?: false
        val storageGranted = permissions[Manifest.permission.READ_EXTERNAL_STORAGE] ?: false
        
        if (!cameraGranted || !storageGranted) {
            showError("Camera and storage permissions are required for this app to work properly")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
        observeViewModel()
        checkPermissions()
    }
    
    private fun setupUI() {
        binding.apply {
            // Camera button
            btnCamera.setOnClickListener {
                if (hasPermissions()) {
                    openCamera()
                } else {
                    requestPermissions()
                }
            }
            
            // Gallery button
            btnGallery.setOnClickListener {
                if (hasPermissions()) {
                    openGallery()
                } else {
                    requestPermissions()
                }
            }
            
            // Analyze button
            btnAnalyze.setOnClickListener {
                currentBitmap?.let { bitmap ->
                    viewModel.classifyImage(bitmap)
                } ?: showError("Please select an image first")
            }
            
            // Clear button
            btnClear.setOnClickListener {
                clearResults()
            }
        }
    }
    
    private fun observeViewModel() {
        viewModel.isLoading.observe(this) { isLoading ->
            binding.apply {
                progressBar.isVisible = isLoading
                btnAnalyze.isEnabled = !isLoading && currentBitmap != null
                btnCamera.isEnabled = !isLoading
                btnGallery.isEnabled = !isLoading
            }
        }
        
        viewModel.classificationResult.observe(this) { result ->
            result?.let { displayResult(it) }
        }
        
        viewModel.error.observe(this) { error ->
            error?.let { 
                showError(it)
                viewModel.clearError()
            }
        }
        
        viewModel.isInitialized.observe(this) { isInitialized ->
            binding.apply {
                if (isInitialized) {
                    tvStatus.text = "AI Model Ready"
                    tvStatus.setTextColor(ContextCompat.getColor(this@MainActivity, android.R.color.holo_green_dark))
                } else {
                    tvStatus.text = "AI Model Loading..."
                    tvStatus.setTextColor(ContextCompat.getColor(this@MainActivity, android.R.color.holo_orange_dark))
                }
            }
        }
    }
    
    private fun handleImageResult(bitmap: Bitmap) {
        currentBitmap = bitmap
        
        // Display the image
        binding.imageView.setImageBitmap(bitmap)
        binding.imageView.isVisible = true
        
        // Enable analyze button
        binding.btnAnalyze.isEnabled = true
        
        // Clear previous results
        clearResults()
        
        Timber.d("Image loaded: ${bitmap.width}x${bitmap.height}")
    }
    
    private fun displayResult(result: devilstudio.com.farmerfriend.data.model.DiseaseResult) {
        binding.apply {
            // Show result container
            resultContainer.isVisible = true
            
            // Display disease name
            tvDiseaseName.text = result.displayName
            
            // Display confidence
            tvConfidence.text = "Confidence: ${result.confidencePercentage}%"
            progressConfidence.progress = result.confidencePercentage
            
            // Display solution (Basic)
            tvSolution.text = result.solution
            
            // Display Rich Details
            val richText = formatRichDetails(result.diseaseInfo)
            if (richText.isNotEmpty()) {
                tvRichDetails.text = richText
                tvRichDetails.isVisible = true
            } else {
                tvRichDetails.isVisible = false
            }
            
            // Display processing time
            tvProcessingTime.text = "Processed in ${result.processingTimeMs}ms"
            
            // Show clear button
            btnClear.isVisible = true
        }
    }
    
    private fun formatRichDetails(info: devilstudio.com.farmerfriend.data.model.DiseaseInfo?): String {
        if (info == null) return ""
        
        val sb = StringBuilder()
        
        // Causes
        info.causes?.let {
            sb.append("\n🔬 ROOT CAUSES\n")
            sb.append(it["details"] ?: "")
            sb.append("\n")
        }
        
        // Prevention
        info.prevention?.let {
            sb.append("\n🛡️ PREVENTION\n")
            it["measures"]?.forEach { measure ->
                sb.append("• $measure\n")
            }
        }
        
        // Treatment
        info.treatment?.stages?.let { stages ->
            sb.append("\n🩺 TREATMENT PLAN\n")
            stages.forEach { stage ->
                sb.append("${stage.name}\n")
                sb.append("${stage.description}\n")
                stage.components?.forEach { comp ->
                    sb.append("- $comp\n")
                }
                sb.append("\n")
            }
        }
        
        // Medications
        info.medications?.let { meds ->
            sb.append("💊 MEDICATIONS\n")
            meds.forEach { med ->
                sb.append("${med.name}: ${med.dosage} (${med.frequency})\n")
            }
            sb.append("\n")
        }
        
        // Emergency
        info.emergency?.let { emerg ->
            sb.append("⚠️ EMERGENCY SIGNS\n")
            sb.append("Action: ${emerg.action}\n")
            emerg.signs?.forEach { sign ->
                sb.append("(!) $sign\n")
            }
        }
        
        return sb.toString()
    }
    
    private fun clearResults() {
        binding.apply {
            resultContainer.isVisible = false
            btnClear.isVisible = false
        }
        viewModel.clearResult()
    }
    
    private fun openCamera() {
        val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        if (intent.resolveActivity(packageManager) != null) {
            cameraLauncher.launch(intent)
        } else {
            showError("Camera not available")
        }
    }
    
    private fun openGallery() {
        val intent = Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI)
        galleryLauncher.launch(intent)
    }
    
    private fun checkPermissions() {
        if (!hasPermissions()) {
            requestPermissions()
        }
    }
    
    private fun hasPermissions(): Boolean {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestPermissions() {
        permissionLauncher.launch(
            arrayOf(
                Manifest.permission.CAMERA,
                Manifest.permission.READ_EXTERNAL_STORAGE
            )
        )
    }
    
    private fun showError(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
        Timber.e("Error: $message")
    }
    
    override fun onDestroy() {
        super.onDestroy()
        currentBitmap?.recycle()
        currentBitmap = null
    }
}



