import { useEffect, useState } from "react"
import { motion } from "framer-motion"

// Define the styles structure matching the backend
interface CaptionStyle {
    Fontname: string
    PrimaryColour: string // &H00BBGGRR
    HighlightColour: string
    OutlineColour: string
    BackColour: string
    BorderStyle: number // 1=Outline, 3=Box
    Outline: number
    Shadow: number
    Alignment: number
    MarginV: number
}

// Ported from src/fast_caption.py
const PRESET_STYLES: Record<string, CaptionStyle> = {
    "Hormozi": {
        Fontname: "The Bold Font",
        PrimaryColour: "&H00FFFFFF",
        HighlightColour: "&H0000FFFF", // Yellow (BGR: 00FFFF)
        OutlineColour: "&H00000000",
        BackColour: "&H80000000",
        BorderStyle: 1,
        Outline: 3,
        Shadow: 0,
        Alignment: 5,
        MarginV: 250,
    },
    "Minimal": {
        Fontname: "Montserrat",
        PrimaryColour: "&H00FFFFFF",
        HighlightColour: "&H00CCCCCC",
        OutlineColour: "&H00000000",
        BackColour: "&H60000000",
        BorderStyle: 1,
        Outline: 1,
        Shadow: 0,
        Alignment: 2,
        MarginV: 50,
    },
    "Neon": {
        Fontname: "Arial Black",
        PrimaryColour: "&H00FFFFFF",
        HighlightColour: "&H00FFFF00", // Cyan (BGR: FFFF00)
        OutlineColour: "&H00FF0080", // Purple/Pink Glow
        BackColour: "&H00000000",
        BorderStyle: 1,
        Outline: 2,
        Shadow: 2,
        Alignment: 5,
        MarginV: 250,
    },
    "Boxed": {
        Fontname: "Arial",
        PrimaryColour: "&H00000000",
        HighlightColour: "&H000000FF", // Red
        OutlineColour: "&H00FFFFFF",
        BackColour: "&H80FFFFFF", // White Box
        BorderStyle: 3,
        Outline: 0,
        Shadow: 0,
        Alignment: 2,
        MarginV: 50,
    },
    "Beast": {
        Fontname: "Komika Axis",
        PrimaryColour: "&H00FFFFFF",
        HighlightColour: "&H000000FF", // Red
        OutlineColour: "&H00000000",
        BackColour: "&H40000000",
        BorderStyle: 1,
        Outline: 5,
        Shadow: 2,
        Alignment: 5,
        MarginV: 300,
    },
     "Gaming": {
        Fontname: "Lilita One",
        PrimaryColour: "&H0000FF00",  // Green
        HighlightColour: "&H00FFFFFF",  // White
        OutlineColour: "&H00000000",  // Black
        BackColour: "&H80000000",
        BorderStyle: 1,
        Outline: 4,
        Shadow: 0,
        Alignment: 5,
        MarginV: 200,
    },
}

const assToCss = (assColor: string): string => {
    if (assColor.startsWith("#")) return assColor
    let hex = assColor.replace("&H", "")
    if (hex.length >= 6) {
        const b = hex.slice(hex.length - 6, hex.length - 4)
        const g = hex.slice(hex.length - 4, hex.length - 2)
        const r = hex.slice(hex.length - 2, hex.length)
        return `#${r}${g}${b}` 
    }
    return "#FFFFFF"
}

interface CaptionPreviewProps {
    style: string
    fontSize: number
    strokeEnabled: boolean
    backEnabled: boolean
    strokeWidth: number
    backAlpha: number
    outlineColor: string
    backColor: string
    customConfig: {
        font: string
        primary_color: string
        highlight_color: string
    }
    isCustom: boolean
    position?: string
}

export function CaptionPreview({ 
    style, 
    fontSize, 
    strokeEnabled,
    backEnabled,
    strokeWidth,
    backAlpha,
    outlineColor,
    backColor,
    customConfig, 
    isCustom, 
    position = "center" 
}: CaptionPreviewProps) {
    const [currentConfig, setCurrentConfig] = useState<CaptionStyle>(PRESET_STYLES["Hormozi"])

    useEffect(() => {
        let baseConfig: CaptionStyle;
        if (isCustom) {
            baseConfig = {
                Fontname: customConfig.font,
                PrimaryColour: customConfig.primary_color,
                HighlightColour: customConfig.highlight_color,
                OutlineColour: outlineColor,
                BackColour: backColor,
                BorderStyle: backEnabled ? 3 : 1, 
                Outline: strokeEnabled ? strokeWidth : 0,
                Shadow: 0,
                Alignment: 5,
                MarginV: 250
            }
        } else {
            // BUG FIX: Strictly clone the preset and ignore custom colors
            baseConfig = { ...PRESET_STYLES[style] || PRESET_STYLES["Hormozi"] }
            
            // Apply global overrides for presets
            if (strokeEnabled) {
                baseConfig.Outline = strokeWidth
                baseConfig.OutlineColour = outlineColor
            } else {
                baseConfig.Outline = 0
            }
            
            if (backEnabled) {
                baseConfig.BorderStyle = 3
                baseConfig.BackColour = backColor
            } else {
                baseConfig.BorderStyle = 1
            }
        }

        // Apply position override
        if (position === "top") {
            baseConfig.Alignment = 8
        } else if (position === "bottom") {
            baseConfig.Alignment = 2
        } else if (position === "center") {
            baseConfig.Alignment = 5
        }

        setCurrentConfig(baseConfig)
    }, [style, customConfig, isCustom, position, strokeEnabled, backEnabled, strokeWidth, backAlpha, outlineColor, backColor])

    const getCssColor = (color: string) => {
        if (color.startsWith("#")) return color
        return assToCss(color)
    }

    const primary = getCssColor(currentConfig.PrimaryColour)
    const highlight = getCssColor(currentConfig.HighlightColour)
    const outline = getCssColor(currentConfig.OutlineColour)
    // Custom alpha handling for background box
    const backBase = getCssColor(currentConfig.BackColour)
    const back = backEnabled ? `${backBase}${Math.floor(backAlpha * 255).toString(16).padStart(2, '0')}` : backBase

    // Scaling factor for preview (60px slider -> normalized size in container)
    const previewScale = fontSize / 60;
    const baseFontSize = 20 * previewScale;
    const highlightFontSize = 26 * previewScale;

    const visualStrokeWidth = currentConfig.Outline * 1.5 * previewScale;
    const shadowWidth = currentConfig.Shadow * 1.5 * previewScale;

    const textShadow = currentConfig.Outline > 0 ? `
        -${visualStrokeWidth}px -${visualStrokeWidth}px 0 ${outline},
        ${visualStrokeWidth}px -${visualStrokeWidth}px 0 ${outline},
        -${visualStrokeWidth}px ${visualStrokeWidth}px 0 ${outline},
        ${visualStrokeWidth}px ${visualStrokeWidth}px 0 ${outline},
        ${shadowWidth}px ${shadowWidth}px 0 rgba(0,0,0,0.5)
    ` : (currentConfig.Shadow > 0 ? `${shadowWidth}px ${shadowWidth}px 0 rgba(0,0,0,0.5)` : "none")

    const boxStyle = currentConfig.BorderStyle === 3 ? {
        backgroundColor: back,
        padding: `${4 * previewScale}px ${12 * previewScale}px`,
        borderRadius: `${4 * previewScale}px`
    } : {}

    const getAlignmentStyles = (alignment: number) => {
        const styles: React.CSSProperties = {
            position: 'absolute',
            display: 'flex',
            flexDirection: 'column',
            width: '100%',
            height: '100%',
            padding: '20px',
            pointerEvents: 'none'
        }
        
        if (alignment >= 7) styles.justifyContent = 'flex-start'
        else if (alignment >= 4) styles.justifyContent = 'center'
        else styles.justifyContent = 'flex-end'

        if ([1, 4, 7].includes(alignment)) styles.alignItems = 'flex-start'
        else if ([2, 5, 8].includes(alignment)) styles.alignItems = 'center'
        else styles.alignItems = 'flex-end'
        
        return styles
    }

    const wordContainerStyle: React.CSSProperties = {
        display: 'flex',
        flexWrap: 'nowrap',
        justifyContent: 'center',
        alignItems: 'baseline',
        gap: `${8 * previewScale}px`,
        padding: `${8 * previewScale}px`,
        textAlign: 'center'
    }

    return (
        <div className="w-full aspect-video bg-zinc-900 rounded-lg overflow-hidden relative border border-white/10 shadow-inner group">
            <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?q=80&w=1000')] bg-cover bg-center opacity-50 grayscale group-hover:grayscale-0 transition-all duration-500" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />

            <div style={getAlignmentStyles(currentConfig.Alignment)}>
                 <div style={{ ...boxStyle, fontFamily: currentConfig.Fontname, fontWeight: 'bold', ...wordContainerStyle }}>
                    <motion.span 
                        style={{ 
                            color: primary, 
                            textShadow: textShadow,
                            fontSize: `${baseFontSize}px`,
                            whiteSpace: 'nowrap'
                        }}
                    >
                        THIS IS
                    </motion.span>
                    
                    <motion.span 
                        initial={{ scale: 0.9 }}
                        animate={{ scale: 1 }}
                        transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
                        style={{ 
                            color: highlight, 
                            textShadow: textShadow,
                            fontSize: `${highlightFontSize}px`, 
                            display: "inline-block",
                            whiteSpace: 'nowrap'
                        }}
                    >
                        AWESOME
                    </motion.span>
                </div>
            </div>

            <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/50 backdrop-blur rounded text-[8px] text-white/50 uppercase tracking-wider font-bold">
                Preview: {isCustom ? "Custom" : style}
            </div>
        </div>
    )
}
