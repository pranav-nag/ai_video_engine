import { useState } from "react"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ColorPicker } from "@/components/ui/color-picker"
import { CaptionPreview } from "@/components/CaptionPreview"
import { Palette, Sparkles, Type, PaintBucket, ChevronUp, ChevronDown, Eye, Layers, Settings2, PenTool } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { motion, AnimatePresence } from "framer-motion"
import { VideoConfig } from "../../App"
import { ScrollArea } from "@/components/ui/scroll-area"

interface TabStyleProps {
    config: VideoConfig
    setConfig: React.Dispatch<React.SetStateAction<VideoConfig>>
    isProcessing: boolean
}

type SubTab = "main" | "effects" | "custom";

const POPULAR_FONTS = [
    "The Bold Font", 
    "Komika Axis", 
    "Lilita One", 
    "Montserrat", 
    "Arial Black", 
    "Impact",
    "Verdana",
    "Courier New"
];

export function TabStyle({ config, setConfig, isProcessing }: TabStyleProps) {
    const [isPreviewOpen, setIsPreviewOpen] = useState(true);
    const [activeSubTab, setActiveSubTab] = useState<SubTab>("main");
    const [isCustomFontInputVisible, setIsCustomFontInputVisible] = useState(false);

    const updateConfig = (key: keyof VideoConfig, value: any) => {
        setConfig(prev => ({ ...prev, [key]: value }))
    }

    const updateCustomConfig = (key: string, value: any) => {
        setConfig(prev => ({ 
            ...prev, 
            custom_config: { ...prev.custom_config, [key]: value } 
        }))
    }

    const handleFontChange = (font: string) => {
        if (font === "custom_manual") {
            setIsCustomFontInputVisible(true);
            // Don't change actual font yet, wait for input
        } else {
            setIsCustomFontInputVisible(false);
            updateConfig("custom_style", true); // Auto-enable custom mode
            updateCustomConfig("font", font);
        }
    };

    // Sub-Tab Definition
    const subTabs: { id: SubTab, label: string, icon: any }[] = [
        { id: "main", label: "Main", icon: Palette },
        { id: "effects", label: "Effects", icon: Layers },
        { id: "custom", label: "Custom", icon: Sparkles },
    ];

    return (
        <div className="flex flex-col h-full bg-zinc-950/20">
            {/* Fixed Preview Header */}
            <div className="shrink-0 z-30 bg-[#09090b] border-b border-white/5 shadow-xl relative">
                <div className="px-6 pt-4 pb-4">
                     <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                            <Eye className={`w-4 h-4 ${isPreviewOpen ? "text-primary" : "text-zinc-500"}`} />
                            <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Live Preview</span>
                        </div>
                        <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-6 w-6 p-0 hover:bg-white/10"
                            onClick={() => setIsPreviewOpen(!isPreviewOpen)}
                        >
                            {isPreviewOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </Button>
                    </div>

                    <AnimatePresence>
                        {isPreviewOpen && (
                            <motion.div 
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden"
                            >
                                <CaptionPreview 
                                    style={config.style} 
                                    fontSize={config.caption_size}
                                    strokeEnabled={config.stroke_enabled}
                                    backEnabled={config.back_enabled}
                                    strokeWidth={config.stroke_width}
                                    backAlpha={config.back_alpha}
                                    outlineColor={config.outline_color}
                                    backColor={config.back_color}
                                    customConfig={config.custom_config} 
                                    isCustom={config.custom_style} 
                                    position={config.caption_pos}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Sub-Tab Navigation */}
                <div className="px-6 pb-0">
                    <div className="flex space-x-1 border-b border-white/10">
                        {subTabs.map((tab) => {
                            const Icon = tab.icon;
                            const isActive = activeSubTab === tab.id;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveSubTab(tab.id)}
                                    className={`
                                        flex items-center space-x-2 px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-b-2 transition-colors relative
                                        ${isActive ? "border-primary text-white" : "border-transparent text-zinc-500 hover:text-zinc-300"}
                                    `}
                                >
                                    <Icon className={`w-3.5 h-3.5 ${isActive ? "text-primary" : ""}`} />
                                    <span>{tab.label}</span>
                                    {isActive && (
                                        <motion.div 
                                            layoutId="subTabIndicator"
                                            className="absolute bottom-[-2px] left-0 right-0 h-0.5 bg-primary shadow-[0_-2px_10px_rgba(124,58,237,0.5)]"
                                        />
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Scrollable Controls Content */}
            <ScrollArea className="flex-1">
                <div className="p-6 space-y-6">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeSubTab}
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            transition={{ duration: 0.15 }}
                            className="space-y-6"
                        >
                            {/* --- MAIN TAB: PRESETS & TYPOGRAPHY --- */}
                            {activeSubTab === "main" && (
                                <>
                                    {/* Style & Position remains here */}
                                    <div className="space-y-3">
                                        <label className="text-xs font-bold text-zinc-400 uppercase ml-1 flex items-center">
                                            <Palette className="w-3.5 h-3.5 mr-1.5" /> Style & Position
                                        </label>
                                        <div className="grid grid-cols-2 gap-3">
                                            <Select 
                                                value={config.style} 
                                                onValueChange={(v) => updateConfig("style", v)}
                                                disabled={config.custom_style || isProcessing}
                                            >
                                                <SelectTrigger className="bg-zinc-900/50 border-white/5 h-10 text-xs">
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent className="bg-zinc-950 border-white/10">
                                                    <SelectItem value="Hormozi">Hormozi</SelectItem>
                                                    <SelectItem value="Beast">MrBeast</SelectItem>
                                                    <SelectItem value="Neon">Neon</SelectItem>
                                                    <SelectItem value="Minimal">Minimal</SelectItem>
                                                    <SelectItem value="Boxed">Boxed</SelectItem>
                                                </SelectContent>
                                            </Select>

                                            <Select 
                                                value={config.caption_pos} 
                                                onValueChange={(v) => updateConfig("caption_pos", v)}
                                                disabled={isProcessing}
                                            >
                                                <SelectTrigger className="bg-zinc-900/50 border-white/5 h-10 text-xs">
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent className="bg-zinc-950 border-white/10">
                                                    <SelectItem value="top">Top</SelectItem>
                                                    <SelectItem value="center">Center</SelectItem>
                                                    <SelectItem value="bottom">Bottom</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>

                                    {/* Font Size Slider Duplication to Main Tab */}
                                    <div className="space-y-3 p-4 bg-zinc-900/30 rounded-xl border border-white/5">
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="text-xs font-bold text-zinc-400 uppercase flex items-center">
                                                <Type className="w-3.5 h-3.5 mr-1.5" /> Font Size
                                            </label>
                                            <span className="font-mono text-primary text-xs font-bold bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
                                                {config.caption_size}px
                                            </span>
                                        </div>
                                        <Slider 
                                            defaultValue={[config.caption_size]} 
                                            min={16} 
                                            max={120} 
                                            step={2}
                                            value={[config.caption_size]}
                                            onValueChange={(val) => updateConfig("caption_size", val[0])}
                                            disabled={isProcessing}
                                            className="py-2"
                                        />
                                    </div>
                                </>
                            )}

                            {/* --- EFFECTS TAB: OUTLINE & BACKGROUND --- */}
                            {activeSubTab === "effects" && (
                                <div className="space-y-4">
                                    {/* Outline Control */}
                                    <div className="p-4 bg-zinc-900/30 rounded-xl border border-white/5 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-3">
                                                <Switch 
                                                    checked={config.stroke_enabled}
                                                    onCheckedChange={(c) => updateConfig("stroke_enabled", c)}
                                                    disabled={isProcessing}
                                                    className="scale-75 data-[state=checked]:bg-primary"
                                                    id="stroke-switch"
                                                />
                                                <label htmlFor="stroke-switch" className="text-xs font-bold text-zinc-400 uppercase cursor-pointer">Text Outline</label>
                                            </div>
                                            <ColorPicker 
                                                color={config.outline_color}
                                                onChange={(c) => updateConfig("outline_color", c)}
                                                disabled={!config.stroke_enabled}
                                                compact={true}
                                                className="border-white/10"
                                            />
                                        </div>
                                        
                                        <AnimatePresence>
                                            {config.stroke_enabled && (
                                                <motion.div 
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: "auto", opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    className="pt-2"
                                                >
                                                    <div className="flex justify-between text-[11px] text-zinc-500 mb-2 uppercase tracking-wider font-bold">Thickness</div>
                                                    <Slider 
                                                        defaultValue={[config.stroke_width]} 
                                                        min={0} 
                                                        max={10} 
                                                        step={0.5}
                                                        value={[config.stroke_width]}
                                                        onValueChange={(val) => updateConfig("stroke_width", val[0])}
                                                        className="py-1"
                                                    />
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>

                                    {/* Background Control */}
                                    <div className="p-4 bg-zinc-900/30 rounded-xl border border-white/5 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-3">
                                                <Switch 
                                                    checked={config.back_enabled}
                                                    onCheckedChange={(c) => updateConfig("back_enabled", c)}
                                                    disabled={isProcessing}
                                                    className="scale-75 data-[state=checked]:bg-primary"
                                                    id="back-switch"
                                                />
                                                <label htmlFor="back-switch" className="text-xs font-bold text-zinc-400 uppercase cursor-pointer">Box Background</label>
                                            </div>
                                            <ColorPicker 
                                                color={config.back_color}
                                                onChange={(c) => updateConfig("back_color", c)}
                                                disabled={!config.back_enabled}
                                                compact={true}
                                                className="border-white/10"
                                            />
                                        </div>

                                        <AnimatePresence>
                                            {config.back_enabled && (
                                                <motion.div 
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: "auto", opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    className="pt-2"
                                                >
                                                    <div className="flex justify-between text-[11px] text-zinc-500 mb-2 uppercase tracking-wider font-bold">Opacity</div>
                                                    <Slider 
                                                        defaultValue={[config.back_alpha]} 
                                                        min={0} 
                                                        max={1} 
                                                        step={0.05}
                                                        value={[config.back_alpha]}
                                                        onValueChange={(val) => updateConfig("back_alpha", val[0])}
                                                        className="py-1"
                                                    />
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </div>
                            )}

                            {/* --- CUSTOM TAB: DETAILED OVERRIDES --- */}
                            {activeSubTab === "custom" && (
                                <div className="space-y-4">
                                     <div className="flex items-center justify-between bg-white/5 p-3 rounded-lg border border-white/5">
                                         <div className="flex items-center space-x-2">
                                            <Sparkles className="w-4 h-4 text-primary" />
                                            <div className="flex flex-col">
                                                <span className="text-xs font-bold text-white uppercase tracking-wider">Override Preset</span>
                                                <span className="text-[10px] text-zinc-500">Enable manual color control</span>
                                            </div>
                                        </div>
                                        <Switch 
                                            checked={config.custom_style}
                                            onCheckedChange={(c) => updateConfig("custom_style", c)}
                                            disabled={isProcessing}
                                            className="data-[state=checked]:bg-primary"
                                        />
                                    </div>

                                    <AnimatePresence>
                                        {config.custom_style && (
                                            <motion.div 
                                                initial={{ opacity: 0, scale: 0.95 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                exit={{ opacity: 0, scale: 0.95 }}
                                                className="space-y-4"
                                            >
                                                {/* Font Customization */}
                                                <div className="space-y-3 p-4 bg-zinc-900/30 rounded-xl border border-white/5">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <label className="text-xs font-bold text-zinc-400 uppercase flex items-center">
                                                            <PenTool className="w-3.5 h-3.5 mr-1.5" /> Font Family
                                                        </label>
                                                    </div>

                                                    <Select 
                                                        value={isCustomFontInputVisible ? "custom_manual" : (POPULAR_FONTS.includes(config.custom_config.font) ? config.custom_config.font : "custom_manual")}
                                                        onValueChange={handleFontChange}
                                                        disabled={isProcessing}
                                                    >
                                                        <SelectTrigger className="bg-zinc-900/50 border-white/5 h-10 text-xs font-medium">
                                                            <SelectValue placeholder="Select Font" />
                                                        </SelectTrigger>
                                                        <SelectContent className="bg-zinc-950 border-white/10 max-h-[300px]">
                                                            {POPULAR_FONTS.map(font => (
                                                                <SelectItem key={font} value={font} style={{ fontFamily: font }}>
                                                                    {font}
                                                                </SelectItem>
                                                            ))}
                                                            <SelectItem value="custom_manual" className="font-mono text-zinc-400 border-t border-white/5 mt-1 pt-2">
                                                                Other (System Font)...
                                                            </SelectItem>
                                                        </SelectContent>
                                                    </Select>

                                                    {isCustomFontInputVisible && (
                                                        <motion.div 
                                                            initial={{ opacity: 0, height: 0 }}
                                                            animate={{ opacity: 1, height: "auto" }}
                                                            className="pt-2"
                                                        >
                                                            <Input 
                                                                placeholder="Enter font name (e.g. Comic Sans MS)"
                                                                className="h-8 text-xs bg-zinc-900/50 border-white/10"
                                                                value={config.custom_config.font}
                                                                onChange={(e) => {
                                                                    updateConfig("custom_style", true)
                                                                    updateCustomConfig("font", e.target.value)
                                                                }}
                                                            />
                                                            <p className="text-[9px] text-zinc-500 mt-1.5 ml-1">
                                                                Make sure the font is installed on your system.
                                                            </p>
                                                        </motion.div>
                                                    )}
                                                </div>

                                                <div className="space-y-3 p-4 bg-zinc-900/30 rounded-xl border border-white/5">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <label className="text-xs font-bold text-zinc-400 uppercase flex items-center">
                                                            <Type className="w-3.5 h-3.5 mr-1.5" /> Font Size
                                                        </label>
                                                        <span className="font-mono text-primary text-xs font-bold bg-primary/10 px-2 py-0.5 rounded border border-primary/20">{config.caption_size}px</span>
                                                    </div>
                                                    <Slider 
                                                        defaultValue={[config.caption_size]} 
                                                        min={16} 
                                                        max={120} 
                                                        step={2}
                                                        value={[config.caption_size]}
                                                        onValueChange={(val) => updateConfig("caption_size", val[0])}
                                                        disabled={isProcessing}
                                                        className="py-2"
                                                    />
                                                </div>

                                                {/* Manual Colors */}
                                                <div className="grid grid-cols-2 gap-3">
                                                    <div className="space-y-2 p-3 bg-zinc-900/40 rounded-lg border border-white/5">
                                                        <label className="text-[11px] text-zinc-400 uppercase font-bold flex items-center">
                                                            <PaintBucket className="w-3 h-3 mr-1.5" /> Fill Color
                                                        </label>
                                                        <ColorPicker 
                                                            color={config.custom_config.primary_color}
                                                            onChange={(c) => updateCustomConfig("primary_color", c)}
                                                            className="w-full h-8"
                                                        />
                                                    </div>
                                                    <div className="space-y-2 p-3 bg-zinc-900/40 rounded-lg border border-white/5">
                                                        <label className="text-[11px] text-zinc-400 uppercase font-bold flex items-center">
                                                            <Sparkles className="w-3 h-3 mr-1.5" /> Pop Color
                                                        </label>
                                                        <ColorPicker 
                                                            color={config.custom_config.highlight_color}
                                                            onChange={(c) => updateCustomConfig("highlight_color", c)}
                                                            className="w-full h-8"
                                                        />
                                                    </div>
                                                </div>

                                                {/* Quick Palettes */}
                                                <div className="space-y-2">
                                                    <label className="text-xs font-bold text-zinc-500 uppercase px-1">Quick Palettes</label>
                                                    <div className="grid grid-cols-4 gap-2">
                                                        {[
                                                            { name: "Cyber", primary: "#8b5cf6", highlight: "#06b6d4" },
                                                            { name: "Ocean", primary: "#0ea5e9", highlight: "#38bdf8" },
                                                            { name: "Sunset", primary: "#f97316", highlight: "#facc15" },
                                                            { name: "Forest", primary: "#22c55e", highlight: "#a3e635" }
                                                        ].map((theme) => (
                                                            <button
                                                                key={theme.name}
                                                                onClick={() => {
                                                                    updateConfig("custom_style", true);
                                                                    updateCustomConfig("primary_color", theme.primary);
                                                                    updateCustomConfig("highlight_color", theme.highlight);
                                                                }}
                                                                className="group relative h-10 rounded-lg overflow-hidden border border-white/10 hover:border-white/30 transition-all shadow-sm"
                                                                title={theme.name}
                                                            >
                                                                <div className="absolute inset-0 flex">
                                                                    <div className="w-1/2 h-full" style={{ backgroundColor: theme.primary }} />
                                                                    <div className="w-1/2 h-full" style={{ backgroundColor: theme.highlight }} />
                                                                </div>
                                                                <div className="absolute inset-0 bg-black/10 group-hover:bg-transparent transition-colors" />
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    {!config.custom_style && (
                                        <div className="p-4 rounded-xl border border-dashed border-white/10 text-center">
                                            <span className="text-[10px] text-zinc-600 block mb-1">Override Disabled</span>
                                            <Button 
                                                variant="outline" 
                                                size="sm" 
                                                className="h-7 text-xs border-white/10 hover:bg-white/5"
                                                onClick={() => updateConfig("custom_style", true)}
                                            >
                                                Activate Custom Mode
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>
                </div>
            </ScrollArea>
        </div>
    )
}
