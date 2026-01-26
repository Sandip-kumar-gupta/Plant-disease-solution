package devilstudio.com.farmerfriend.data.model

data class DiseaseResult(
    val disease: String,
    val confidence: Float,
    val solution: String,
    val processingTimeMs: Long = 0L,
    val diseaseInfo: DiseaseInfo? = null
) {
    val isHealthy: Boolean
        get() = disease.contains("healthy", ignoreCase = true)
    
    val isBackground: Boolean
        get() = disease.equals("background", ignoreCase = true)
    
    val displayName: String
        get() = disease.replace("___", " - ").replace("_", " ").replaceFirstChar { 
            if (it.isLowerCase()) it.titlecase() else it.toString() 
        }
    
    val confidencePercentage: Int
        get() = (confidence * 100).toInt()
}

data class DiseaseInfo(
    val name: String,
    val causes: Map<String, String>?,
    val prevention: Map<String, List<String>>?,
    val treatment: Treatment?,
    val medications: List<Medication>?,
    val emergency: Emergency?,
    val recovery: Recovery?
)

data class Treatment(
    val stages: List<Stage>?
)

data class Stage(
    val name: String,
    val description: String,
    val components: List<String>?,
    val medications: List<String>?
)

data class Medication(
    val name: String,
    val dosage: String?,
    val frequency: String?,
    val side_effects: String?
)

data class Emergency(
    val signs: List<String>?,
    val action: String?
)

data class Recovery(
    val timeline: List<String>?,
    val success_rate: String?
)

data class Classification(
    val id: String = "",
    val title: String = "",
    val confidence: Float = 0f
) {
    override fun toString(): String {
        return "Title = $title, Confidence = $confidence"
    }
}