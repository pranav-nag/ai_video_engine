import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { PlayCircle, Palette, Sparkles, XCircle, Wand2, ArrowRight } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { VideoConfig } from "../App"
import { TabMedia } from "./sidebar/TabMedia"
import { TabAI } from "./sidebar/TabAI"
import { TabStyle } from "./sidebar/TabStyle"

// Helper: Hex to Tailwind HSL format
function hexToHsl(hex: string) {
    hex = hex.replace(/^#/, '');
    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
    
    let r = parseInt(hex.substring(0, 2), 16) / 255;
    let g = parseInt(hex.substring(2, 4), 16) / 255;
    let b = parseInt(hex.substring(4, 6), 16) / 255;

    let max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;

    if (max !== min) {
        let d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }
    return `${(h * 360).toFixed(1)} ${(s * 100).toFixed(1)}% ${(l * 100).toFixed(1)}%`;
}

interface SidebarProps {
    config: VideoConfig
    setConfig: React.Dispatch<React.SetStateAction<VideoConfig>>
    onProcess: () => void
    onCancel: () => void
    onFetchMetadata: () => void
    isProcessing: boolean
    isFetchingMetadata: boolean
    videoMetadata: { title: string; duration: number } | null
    progress: number
    progressPhase: { name: string, percent: number, text: string } | null
}

type TabType = "media" | "ai" | "style";

export function Sidebar({ 
    config, 
    setConfig, 
    onProcess, 
    onCancel, 
    onFetchMetadata,
    isProcessing,
    isFetchingMetadata,
    videoMetadata,
    progress,
    progressPhase 
}: SidebarProps) {

    const [activeTab, setActiveTab] = useState<TabType>("media");

    const tabs: { id: TabType; label: string }[] = [
        { id: "media", label: "Media" },
        { id: "ai", label: "Intelligence" },
        { id: "style", label: "Aesthetics" },
    ];

    return (
        <motion.div 
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="w-[500px] bg-zinc-950/95 backdrop-blur-xl border-r border-white/10 flex flex-col h-full shadow-2xl z-50 fixed left-0 top-0 bottom-0 overflow-hidden"
        >
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex items-center justify-between bg-zinc-950/50 shrink-0 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent pointer-events-none" />
                
                <div className="flex items-center space-x-3 relative z-10">
                    <div className="h-10 w-10 bg-gradient-to-br from-primary/20 to-primary/5 rounded-xl flex items-center justify-center border border-primary/20 shadow-[0_0_15px_rgba(124,58,237,0.15)]">
                        <PlayCircle className="text-primary h-6 w-6" />
                    </div>
                    <div>
                        <h1 className="font-display font-bold text-xl text-white tracking-tight">AI Engine</h1>
                        <span className="text-[10px] uppercase tracking-widest text-primary/80 font-bold ml-0.5">Creator Suite</span>
                    </div>
                </div>

                 {/* Interface Theme Picker */}
                <div className="flex items-center relative z-10">
                    <Popover>
                        <PopoverTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-white hover:bg-white/5 data-[state=open]:text-white">
                                <Palette className="w-4 h-4" />
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-64 p-4 bg-zinc-950/95 backdrop-blur-3xl border border-white/10 shadow-2xl rounded-xl mr-2" align="start" sideOffset={10}>
                            <label className="text-[10px] font-bold text-zinc-500 uppercase mb-3 block">Interface Accent</label>
                            <div className="grid grid-cols-4 gap-2">
                                {[
                                    { name: "Violet", hex: "#7c3aed" },
                                    { name: "Blue", hex: "#3b82f6" },
                                    { name: "Cyan", hex: "#06b6d4" },
                                    { name: "Emerald", hex: "#10b981" },
                                    { name: "Amber", hex: "#f59e0b" },
                                    { name: "Orange", hex: "#f97316" },
                                    { name: "Rose", hex: "#f43f5e" },
                                    { name: "Fuchsia", hex: "#d946ef" }
                                ].map((color) => (
                                    <button
                                        key={color.name}
                                        onClick={() => {
                                            const hsl = hexToHsl(color.hex);
                                            document.documentElement.style.setProperty('--primary', hsl);
                                            document.documentElement.style.setProperty('--ring', hsl);
                                        }}
                                        className="h-9 w-9 rounded-lg border border-white/10 hover:border-white/30 hover:scale-105 transition-all relative group overflow-hidden"
                                        title={color.name}
                                        style={{ backgroundColor: color.hex }}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-tr from-black/20 to-transparent" />
                                        <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity" />
                                    </button>
                                ))}
                            </div>
                        </PopoverContent>
                    </Popover>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="px-6 pt-4 pb-2 bg-zinc-950/30">
                <div className="flex p-1 bg-zinc-900/80 rounded-xl border border-white/5 relative">
                    {/* Animated Background */}
                    <motion.div 
                        className="absolute top-1 bottom-1 rounded-lg bg-zinc-800 shadow-sm border border-white/5 z-0"
                         layoutId="activeTab"
                         initial={false}
                         transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                         style={{ 
                             width: `calc(33.33% - 4px)`, 
                             left: activeTab === "media" ? "4px" : activeTab === "ai" ? "calc(33.33% + 2px)" : "calc(66.66%)"
                         }}
                    />

                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`
                                flex-1 relative z-10 py-1.5 text-[11px] font-bold uppercase tracking-wide transition-colors duration-200
                                ${activeTab === tab.id ? "text-white" : "text-zinc-500 hover:text-zinc-300"}
                            `}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Tab Content Area - No Global Scroll, delegate to tabs */}
            <div className="flex-1 overflow-hidden bg-zinc-950/20 relative">
                 <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2 }}
                        className="h-full"
                    >
                        {activeTab === "media" && (
                            <TabMedia 
                                config={config} 
                                setConfig={setConfig} 
                                onFetchMetadata={onFetchMetadata}
                                isFetchingMetadata={isFetchingMetadata}
                                isProcessing={isProcessing}
                                videoMetadata={videoMetadata}
                            />
                        )}
                        {activeTab === "ai" && (
                            <TabAI 
                                config={config} 
                                setConfig={setConfig} 
                                isProcessing={isProcessing}
                            />
                        )}
                        {activeTab === "style" && (
                            <TabStyle 
                                config={config} 
                                setConfig={setConfig} 
                                isProcessing={isProcessing}
                            />
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>

            {/* Footer Actions */}
            <div className="p-6 border-t border-white/10 bg-zinc-950/80 backdrop-blur-xl shrink-0 z-10 relative">
                {isProcessing ? (
                    <div className="space-y-4">
                        <div className="flex justify-between text-xs text-zinc-400 font-medium">
                            <span className="animate-pulse text-primary flex items-center font-bold tracking-wide">
                                <Wand2 className="w-3.5 h-3.5 mr-2 animate-spin" /> 
                                PROCESSING
                            </span>
                            <span className="font-mono text-white">{Math.round(progress)}%</span>
                        </div>
                        <div className="h-2 bg-zinc-900 rounded-full overflow-hidden border border-white/5">
                            <motion.div 
                                className="h-full bg-gradient-to-r from-primary to-purple-400" 
                                initial={{ width: 0 }}
                                animate={{ width: `${progress}%` }}
                                transition={{ ease: "easeOut" }}
                            />
                        </div>
                        
                        {/* Phase Progress (Sub-bar) */}
                        {progressPhase && (
                             <div className="space-y-1 mt-2">
                                <div className="flex justify-between text-[10px] text-zinc-500 font-mono uppercase tracking-wider">
                                    <span>{progressPhase.text}</span>
                                    <span>{Math.round(progressPhase.percent)}%</span>
                                </div>
                                <div className="h-1 bg-zinc-900 rounded-full overflow-hidden border border-white/5">
                                    <motion.div 
                                        className="h-full bg-zinc-500" 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progressPhase.percent}%` }}
                                        transition={{ ease: "linear" }}
                                    />
                                </div>
                             </div>
                        )}
                        <Button 
                            variant="destructive" 
                            className="w-full h-10 text-xs font-bold tracking-wider" 
                            onClick={onCancel}
                        >
                            <XCircle className="h-3.5 w-3.5 mr-2" /> CANCEL OPERATION
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-3">
                         {/* Navigation Hint if not on last tab */}
                        {activeTab !== "style" && !config.url && (
                            <div className="text-center">
                                <span className="text-[10px] text-zinc-500 animate-pulse">Paste a URL to get started</span>
                            </div>
                        )}

                        <Button 
                            variant="cyber"
                            size="xl"
                            className="w-full h-12 text-sm shadow-[0_0_30px_rgba(124,58,237,0.25)] hover:shadow-[0_0_50px_rgba(124,58,237,0.4)] border-primary/50 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 transition-all duration-300"
                            onClick={onProcess}
                            disabled={!config.url}
                        >
                            <Sparkles className="h-5 w-5 mr-3 animate-pulse text-white" /> 
                            <span className="font-bold tracking-widest text-white">GENERATE CLIPS</span>
                        </Button>
                    </div>
                )}
            </div>
        </motion.div>
    )
}
