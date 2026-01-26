package devilstudio.com.farmerfriend.data.repository

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.qualifiers.ApplicationContext
import devilstudio.com.farmerfriend.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import timber.log.Timber
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DiseaseRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val gson: Gson
) {
    
    private var diseaseDbCache: Map<String, DiseaseInfo>? = null
    
    suspend fun getDiseaseInfo(diseaseName: String): DiseaseInfo = withContext(Dispatchers.IO) {
        if (diseaseDbCache == null) {
            loadDiseaseDatabase()
        }
        
        val normalizedKey = diseaseName.replace("___", "_")
            .replace(" ", "_")
            .lowercase()
            .trim()
            
        // Try to find in DB
        val info = diseaseDbCache?.get(normalizedKey)
        
        if (info != null) {
            return@withContext info
        }
        
        // Fallback: Generate Rich Data for Plant Diseases (Mirroring Web App Logic)
        val displayName = diseaseName.replace("___", " - ").replace("_", " ").replaceFirstChar { 
            if (it.isLowerCase()) it.titlecase() else it.toString() 
        }
        
        val solution = "Remove infected leaves. Apply fungicides if severe." // Basic fallback
        
        return@withContext DiseaseInfo(
            name = displayName,
            causes = mapOf(
                "primary" to "Fungal or bacterial infection associated with $displayName.",
                "details" to "This condition is typically caused by pathogens that thrive in specific environmental conditions. It spreads through water splashes, wind, or contaminated tools. High humidity and poor air circulation often exacerbate the spread."
            ),
            prevention = mapOf(
                "measures" to listOf(
                    "Maintain proper plant spacing to ensure good airflow.",
                    "Water at the base of the plant to avoid wetting foliage.",
                    "Remove and destroy infected leaves immediately.",
                    "Apply preventive organic fungicides early in the season.",
                    "Rotate crops to prevent soil-borne pathogen buildup.",
                    "Use disease-resistant plant varieties where possible.",
                    "Sanitize gardening tools between uses."
                )
            ),
            treatment = Treatment(
                stages = listOf(
                    Stage(
                        name = "Stage 1: Early Detection (Days 1-7)",
                        description = "Immediate isolation and removal of affected parts.",
                        components = listOf(
                            "Isolate the plant to prevent spread to others.",
                            "Prune all visible infected leaves.",
                            "Improve air circulation around the plant."
                        ),
                        medications = listOf("Copper Fungicide Spray")
                    ),
                    Stage(
                        name = "Stage 2: Active Treatment (Days 7-21)",
                        description = "Intensive treatment to halt disease progression.",
                        components = listOf(
                            "Apply fungicide every 7-10 days.",
                            "Monitor daily for new lesions.",
                            "Reduce watering frequency to lower humidity."
                        ),
                        medications = listOf("Mancozeb", "Neem Oil")
                    ),
                    Stage(
                        name = "Stage 3: Recovery (Days 21-60)",
                        description = "Maintenance and monitoring for recurrence.",
                        components = listOf(
                            "Resume normal care but keep foliage dry.",
                            "Apply preventive spray monthly.",
                            "Strengthen plant immunity with organic compost."
                        ),
                        medications = emptyList()
                    )
                )
            ),
            medications = listOf(
                Medication(
                    name = "Copper Fungicide",
                    dosage = "2-3 tablespoons per gallon of water",
                    frequency = "Every 7-10 days",
                    side_effects = "May cause leaf burn in very hot weather."
                ),
                Medication(
                    name = "Neem Oil (Organic)",
                    dosage = "1-2 tablespoons per gallon",
                    frequency = "Every 7-14 days",
                    side_effects = "Safe for most plants, avoid direct sun after application."
                )
            ),
            emergency = Emergency(
                signs = listOf(
                    "More than 50% of leaves are affected.",
                    "Disease has spread to the main stem.",
                    "Plant is wilting rapidly despite watering.",
                    "No improvement after 2 weeks of treatment."
                ),
                action = "Consult an agricultural expert immediately. It may be necessary to remove and destroy the entire plant to save the rest of your garden."
            ),
            recovery = Recovery(
                timeline = listOf(
                    "Week 1: Stop disease spread",
                    "Week 2-3: New healthy growth appears",
                    "Week 4-8: Full recovery expected"
                ),
                success_rate = "85-90% with early treatment"
            )
        )
    }
    
    suspend fun getSolution(diseaseName: String): String {
        val info = getDiseaseInfo(diseaseName)
        // Extract a simple string solution for backward compatibility
        return info.treatment?.stages?.firstOrNull()?.description ?: "No solution available."
    }
    
    private suspend fun loadDiseaseDatabase() = withContext(Dispatchers.IO) {
        try {
            // Try loading the new rich DB first
            val jsonString = context.assets.open("DISEASE_DATABASE.json").bufferedReader().use { it.readText() }
            val type = object : TypeToken<Map<String, DiseaseInfo>>() {}.type
            diseaseDbCache = gson.fromJson(jsonString, type)
            Timber.d("Loaded ${diseaseDbCache?.size} rich disease entries")
        } catch (e: IOException) {
            Timber.e(e, "Error loading DISEASE_DATABASE.json, falling back to empty")
            diseaseDbCache = emptyMap()
        }
    }
}