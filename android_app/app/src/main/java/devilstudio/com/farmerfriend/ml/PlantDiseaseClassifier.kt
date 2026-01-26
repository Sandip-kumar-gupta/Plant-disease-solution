package devilstudio.com.farmerfriend.ml

import android.content.Context
import android.graphics.Bitmap
import dagger.hilt.android.qualifiers.ApplicationContext
import devilstudio.com.farmerfriend.BuildConfig
import devilstudio.com.farmerfriend.data.model.Classification
import devilstudio.com.farmerfriend.data.model.DiseaseResult
import devilstudio.com.farmerfriend.data.repository.DiseaseRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import timber.log.Timber
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PlantDiseaseClassifier @Inject constructor(
    @ApplicationContext private val context: Context,
    private val diseaseRepository: DiseaseRepository
) {
    
    private var interpreter: Interpreter? = null
    private var labels: List<String> = emptyList()
    
    private val inputSize = BuildConfig.MODEL_INPUT_SIZE
    private val pixelSize = 3
    private val imageMean = 0f
    private val imageStd = 255.0f
    private val maxResults = 3
    private val threshold = 0.4f
    
    suspend fun initialize(): Boolean = withContext(Dispatchers.IO) {
        try {
            Timber.d("Initializing PlantDiseaseClassifier...")
            
            // Load model
            val modelBuffer = loadModelFile(BuildConfig.MODEL_PATH)
            interpreter = Interpreter(modelBuffer)
            
            // Load labels
            labels = loadLabels(BuildConfig.LABELS_PATH)
            
            Timber.d("Classifier initialized successfully with ${labels.size} labels")
            true
        } catch (e: Exception) {
            Timber.e(e, "Failed to initialize classifier")
            false
        }
    }
    
    suspend fun classifyImage(bitmap: Bitmap): DiseaseResult? = withContext(Dispatchers.IO) {
        val startTime = System.currentTimeMillis()
        
        try {
            val interpreter = this@PlantDiseaseClassifier.interpreter
                ?: throw IllegalStateException("Classifier not initialized")
            
            // Preprocess image
            val input = preprocessImage(bitmap)
            
            // Run inference
            val output = Array(1) { FloatArray(labels.size) }
            interpreter.run(input, output)
            
            // Get top prediction
            val predictions = output[0]
            val topIndex = predictions.indices.maxByOrNull { predictions[it] } ?: 0
            val confidence = predictions[topIndex]
            
            if (confidence < threshold) {
                Timber.d("Confidence $confidence below threshold $threshold")
                return@withContext null
            }
            
            val diseaseName = if (topIndex < labels.size) labels[topIndex] else "unknown"
            val diseaseInfo = diseaseRepository.getDiseaseInfo(diseaseName)
            val solution = diseaseRepository.getSolution(diseaseName) // Keep for backward compat if needed, or extract from info
            val processingTime = System.currentTimeMillis() - startTime
            
            Timber.d("Classification: $diseaseName (${(confidence * 100).toInt()}%) in ${processingTime}ms")
            
            DiseaseResult(
                disease = diseaseName,
                confidence = confidence,
                solution = solution,
                processingTimeMs = processingTime,
                diseaseInfo = diseaseInfo
            )
        } catch (e: Exception) {
            Timber.e(e, "Error during classification")
            null
        }
    }
    
    suspend fun getTopPredictions(bitmap: Bitmap, count: Int = maxResults): List<Classification> = withContext(Dispatchers.IO) {
        try {
            val interpreter = this@PlantDiseaseClassifier.interpreter
                ?: throw IllegalStateException("Classifier not initialized")
            
            val input = preprocessImage(bitmap)
            val output = Array(1) { FloatArray(labels.size) }
            interpreter.run(input, output)
            
            val predictions = output[0]
            
            predictions.indices
                .map { index -> 
                    Classification(
                        id = index.toString(),
                        title = if (index < labels.size) labels[index] else "unknown",
                        confidence = predictions[index]
                    )
                }
                .filter { it.confidence >= threshold }
                .sortedByDescending { it.confidence }
                .take(count)
        } catch (e: Exception) {
            Timber.e(e, "Error getting top predictions")
            emptyList()
        }
    }
    
    private fun preprocessImage(bitmap: Bitmap): ByteBuffer {
        val resizedBitmap = Bitmap.createScaledBitmap(bitmap, inputSize, inputSize, true)
        
        val byteBuffer = ByteBuffer.allocateDirect(4 * inputSize * inputSize * pixelSize)
        byteBuffer.order(ByteOrder.nativeOrder())
        
        val intValues = IntArray(inputSize * inputSize)
        resizedBitmap.getPixels(intValues, 0, resizedBitmap.width, 0, 0, resizedBitmap.width, resizedBitmap.height)
        
        var pixel = 0
        for (i in 0 until inputSize) {
            for (j in 0 until inputSize) {
                val value = intValues[pixel++]
                
                // Extract RGB values and normalize
                byteBuffer.putFloat(((value shr 16 and 0xFF) - imageMean) / imageStd)
                byteBuffer.putFloat(((value shr 8 and 0xFF) - imageMean) / imageStd)
                byteBuffer.putFloat(((value and 0xFF) - imageMean) / imageStd)
            }
        }
        
        return byteBuffer
    }
    
    private fun loadModelFile(modelPath: String): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd(modelPath)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        val startOffset = fileDescriptor.startOffset
        val declaredLength = fileDescriptor.declaredLength
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
    }
    
    private fun loadLabels(labelPath: String): List<String> {
        return context.assets.open(labelPath).bufferedReader().useLines { it.toList() }
    }
    
    fun isInitialized(): Boolean = interpreter != null && labels.isNotEmpty()
    
    fun cleanup() {
        interpreter?.close()
        interpreter = null
        labels = emptyList()
        Timber.d("Classifier cleaned up")
    }
}