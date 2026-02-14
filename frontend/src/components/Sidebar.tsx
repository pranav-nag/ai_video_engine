import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { PlayCircle, Download, XCircle, Wand2, Palette, Sparkles, MonitorPlay, Timer, Settings2, Scissors } from "lucide-react"
import { ColorPicker } from "@/components/ui/color-picker"
import { VideoConfig } from "../App"
import { motion } from "framer-motion"

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
}

export function Sidebar({ 
    config, 
    setConfig, 
    onProcess, 
    onCancel, 
    onFetchMetadata,
    isProcessing,
    isFetchingMetadata,
    videoMetadata,
    progress 
}: SidebarProps) {

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60)
        const s = Math.floor(seconds % 60)
        return `${m}:${s < 10 ? '0' : ''}${s}`
    }

    const updateConfig = (key: keyof VideoConfig, value: any) => {
        setConfig(prev => ({ ...prev, [key]: value }))
    }

    const updateCustomConfig = (key: string, value: any) => {
        setConfig(prev => ({ 
            ...prev, 
            custom_config: { ...prev.custom_config, [key]: value } 
        }))
    }

    return (
        <motion.div 
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="w-[480px] bg-zinc-950/95 backdrop-blur-xl border-r border-white/10 flex flex-col h-full shadow-2xl z-50 fixed left-0 top-0 bottom-0"
        >
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex items-center justify-between bg-zinc-950/50 shrink-0">
                <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 bg-primary/20 rounded-xl flex items-center justify-center border border-primary/20 shadow-[0_0_15px_rgba(124,58,237,0.3)]">
                        <PlayCircle className="text-primary h-6 w-6" />
                    </div>
                    <div>
                        <h1 className="font-display font-bold text-xl text-white tracking-tight">AI Engine</h1>
                        <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-medium ml-0.5">Pro Studio</span>
                    </div>
                </div>

                 {/* Interface Theme Picker */}
                <div className="flex items-center">
                    <Popover>
                        <PopoverTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-white hover:bg-white/5">
                                <Palette className="w-4 h-4" />
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-56 p-3 bg-zinc-950/95 backdrop-blur-xl border border-white/10" align="end">
                            <label className="text-[10px] font-semibold text-zinc-500 uppercase mb-2 block">Interface Theme</label>
                            <div className="grid grid-cols-4 gap-2">
                                {[
                                    { name: "Violet", hex: "#7c3aed" },
                                    { name: "Blue", hex: "#2563eb" },
                                    { name: "Orange", hex: "#ea580c" },
                                    { name: "Green", hex: "#16a34a" },
                                    { name: "Pink", hex: "#db2777" },
                                    { name: "Red", hex: "#dc2626" },
                                    { name: "Cyan", hex: "#0891b2" },
                                    { name: "Yellow", hex: "#ca8a04" }
                                ].map((color) => (
                                    <button
                                        key={color.name}
                                        onClick={() => {
                                            const hsl = hexToHsl(color.hex);
                                            document.documentElement.style.setProperty('--primary', hsl);
                                            document.documentElement.style.setProperty('--ring', hsl);
                                        }}
                                        className="h-8 w-8 rounded-full border border-white/10 hover:scale-110 transition-transform relative group"
                                        title={color.name}
                                        style={{ backgroundColor: color.hex }}
                                    >
                                        <div className="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-20 transition-opacity" />
                                    </button>
                                ))}
                            </div>
                        </PopoverContent>
                    </Popover>
                </div>
            </div>

            <ScrollArea className="flex-1">
                <div className="p-6 space-y-8 pb-32">
                {/* section 1: Input */}
                <section className="space-y-4">
                    <div className="flex items-center space-x-2 text-zinc-400 mb-2">
                        <Download className="w-4 h-4 text-primary" />
                        <h3 className="text-xs font-bold uppercase tracking-widest">Source Media</h3>
                    </div>
                    
                    <div className="p-1 bg-zinc-900/50 rounded-lg border border-white/5 space-y-3">
                        <div className="flex space-x-2 p-2">
                            <Input 
                                placeholder="Paste YouTube URL..." 
                                className="bg-zinc-950/50 border-white/10 focus:ring-primary text-sm h-10"
                                value={config.url}
                                onChange={(e) => updateConfig("url", e.target.value)}
                                disabled={isProcessing}
                            />
                            <Button 
                                className="bg-zinc-800 hover:bg-zinc-700 h-10 w-12"
                                onClick={onFetchMetadata}
                                disabled={!config.url || isProcessing || isFetchingMetadata}
                            >
                                {isFetchingMetadata ? <Wand2 className="w-4 h-4 animate-spin text-primary" /> : <Sparkles className="w-4 h-4 text-primary" />}
                            </Button>
                        </div>

                        {videoMetadata && (
                            <motion.div 
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="px-3 pb-3"
                            >
                                <div className="p-3 bg-primary/5 rounded border border-primary/10 space-y-1">
                                    <div className="text-zinc-200 font-medium truncate text-xs flex items-center">
                                        <MonitorPlay className="w-3 h-3 mr-2 text-primary" />
                                        {videoMetadata.title}
                                    </div>
                                    <div className="text-zinc-500 text-[10px] pl-5 flex items-center">
                                        <Timer className="w-3 h-3 mr-1" />
                                        {formatTime(videoMetadata.duration)}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </div>
                </section>

                <Separator className="bg-white/5" />

                {/* Section: Trimming */}
                 <section className="space-y-4">
                    <div className="flex items-center space-x-2 text-zinc-400 mb-2">
                        <Scissors className="w-4 h-4 text-primary" />
                        <h3 className="text-xs font-bold uppercase tracking-widest">Trim Source</h3>
                    </div>

                    <div className="p-4 bg-zinc-900/30 rounded-lg border border-white/5 space-y-4">
                        {/* Time Inputs */}
                        <div className="flex items-center justify-between gap-2">
                            <div className="space-y-1 w-full">
                                <label className="text-[10px] text-zinc-500 uppercase font-bold">Start</label>
                                <Input 
                                    className="h-8 bg-zinc-950 border-white/10 text-xs font-mono text-center"
                                    value={formatTime(parseInt(config.start_time) || 0)}
                                    readOnly
                                />
                            </div>
                            <div className="text-zinc-600 font-mono">-</div>
                            <div className="space-y-1 w-full">
                                <label className="text-[10px] text-zinc-500 uppercase font-bold">End</label>
                                <Input 
                                    className="h-8 bg-zinc-950 border-white/10 text-xs font-mono text-center"
                                    value={videoMetadata ? formatTime(parseInt(config.end_time) || videoMetadata.duration) : "Full"}
                                    readOnly
                                />
                            </div>
                        </div>

                        {/* Slider */}
                        <div className="pt-2 pb-1">
                             <Slider 
                                defaultValue={[0, videoMetadata?.duration || 100]} 
                                min={0} 
                                max={videoMetadata?.duration || 100} 
                                step={1}
                                value={[
                                    parseInt(config.start_time) || 0, 
                                    parseInt(config.end_time) || (videoMetadata?.duration || 100)
                                ]}
                                onValueChange={(val) => {
                                    setConfig(prev => ({ 
                                        ...prev, 
                                        start_time: val[0].toString(), 
                                        end_time: val[1].toString() 
                                    }))
                                }}
                                disabled={!videoMetadata || isProcessing}
                                className="py-2"
                            />
                        </div>

                        {/* Presets */}
                         <div className="grid grid-cols-3 gap-2">
                            <Badge 
                                variant="outline" 
                                className="justify-center cursor-pointer hover:bg-white/5 hover:text-white text-zinc-500 h-7 text-[10px]"
                                onClick={() => videoMetadata && setConfig(prev => ({ ...prev, start_time: "0", end_time: videoMetadata.duration.toString() }))}
                            >
                                Full
                            </Badge>
                             <Badge 
                                variant="outline" 
                                className="justify-center cursor-pointer hover:bg-white/5 hover:text-white text-zinc-500 h-7 text-[10px]"
                                onClick={() => setConfig(prev => ({ ...prev, start_time: "0", end_time: "600" }))}
                            >
                                First 10m
                            </Badge>
                             <Badge 
                                variant="outline" 
                                className="justify-center cursor-pointer hover:bg-white/5 hover:text-white text-zinc-500 h-7 text-[10px]"
                                onClick={() => videoMetadata && setConfig(prev => ({ ...prev, start_time: Math.max(0, videoMetadata.duration - 600).toString(), end_time: videoMetadata.duration.toString() }))}
                            >
                                Last 10m
                            </Badge>
                        </div>
                    </div>
                </section>


                <Separator className="bg-white/5" />

                {/* Section 2: Strategy */}
                <section className="space-y-4">
                    <div className="flex items-center space-x-2 text-zinc-400 mb-2">
                        <Settings2 className="w-4 h-4 text-primary" />
                        <h3 className="text-xs font-bold uppercase tracking-widest">AI Strategy</h3>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        {/* Focus Mode */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-semibold text-zinc-500 uppercase">Focus</label>
                            <Select 
                                value={config.focus_mode} 
                                onValueChange={(v) => updateConfig("focus_mode", v)}
                                disabled={isProcessing}
                            >
                                <SelectTrigger className="bg-zinc-900/50 border-white/5 h-9">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-zinc-950 border-white/10">
                                    <SelectItem value="center">Center Crop</SelectItem>
                                    <SelectItem value="auto-face">Auto Face Detection</SelectItem>
                                    <SelectItem value="left">Left Third</SelectItem>
                                    <SelectItem value="right">Right Third</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                         {/* Content Type */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-semibold text-zinc-500 uppercase">Genre</label>
                            <Select 
                                value={config.content_type} 
                                onValueChange={(v) => updateConfig("content_type", v)}
                                disabled={isProcessing}
                            >
                                <SelectTrigger className="bg-zinc-900/50 border-white/5 h-9">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-zinc-950 border-white/10">
                                    <SelectItem value="General">General</SelectItem>
                                    <SelectItem value="Podcast">Podcast</SelectItem>
                                    <SelectItem value="Motivational">Motivational</SelectItem>
                                    <SelectItem value="Gaming">Gaming</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {/* Duration Slider */}
                    <div className="space-y-3 pt-2 p-4 bg-zinc-900/30 rounded-lg border border-white/5">
                        <div className="flex justify-between text-xs items-center">
                            <label className="text-zinc-400 font-medium">Clip Duration</label>
                            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 py-0 h-5">
                                {config.min_sec}s - {config.max_sec}s
                            </Badge>
                        </div>
                        <Slider 
                            defaultValue={[30, 60]} 
                            min={5} 
                            max={120} 
                            step={5}
                            value={[config.min_sec, config.max_sec]}
                            onValueChange={(val) => {
                                setConfig(prev => ({ ...prev, min_sec: val[0], max_sec: val[1] }))
                            }}
                            disabled={isProcessing}
                            className="py-2"
                        />
                    </div>
                </section>

                <Separator className="bg-white/5" />

                {/* Section 3: Aesthetics */}
                <section className="space-y-4">
                    <div className="flex items-center justify-between text-zinc-400 mb-2">
                        <div className="flex items-center space-x-2">
                            <Palette className="w-4 h-4 text-primary" />
                            <h3 className="text-xs font-bold uppercase tracking-widest">Aesthetics</h3>
                        </div>
                        <div className="flex items-center space-x-2">
                             <span className="text-[10px] text-zinc-600 font-bold uppercase">Custom</span>
                             <Switch 
                                checked={config.custom_style}
                                onCheckedChange={(c) => updateConfig("custom_style", c)}
                                disabled={isProcessing}
                                className="scale-75 data-[state=checked]:bg-primary"
                             />
                        </div>
                    </div>

                    {/* Style & Res */}
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-semibold text-zinc-500 uppercase">Caption Preset</label>
                            <Select 
                                value={config.style} 
                                onValueChange={(v) => updateConfig("style", v)}
                                disabled={config.custom_style || isProcessing}
                            >
                                <SelectTrigger className="bg-zinc-900/50 border-white/5 h-10">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-zinc-950 border-white/10">
                                    <SelectItem value="Hormozi">Hormozi (Bold)</SelectItem>
                                    <SelectItem value="Beast">MrBeast (Vibrant)</SelectItem>
                                    <SelectItem value="Neon">Neon (Glow)</SelectItem>
                                    <SelectItem value="Minimal">Minimal (Clean)</SelectItem>
                                    <SelectItem value="Boxed">Boxed (Black)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                     {/* Quick Themes & Custom Colors - Collapsible */}
                     {config.custom_style && (
                        <motion.div 
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            className="p-4 bg-zinc-900/30 rounded-xl border border-white/5 space-y-4 overflow-hidden"
                        >
                             <div className="space-y-2">
                                <label className="text-[10px] font-semibold text-zinc-500 uppercase mb-2 block">Quick Themes</label>
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
                                            className="group relative h-8 rounded-lg overflow-hidden border border-white/10 hover:border-white/30 transition-all"
                                            title={theme.name}
                                        >
                                            <div className="absolute inset-0 flex">
                                                <div className="w-1/2 h-full" style={{ backgroundColor: theme.primary }} />
                                                <div className="w-1/2 h-full" style={{ backgroundColor: theme.highlight }} />
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            
                            <div className="pt-2 border-t border-white/5">
                                <label className="text-[10px] font-semibold text-zinc-500 uppercase mb-2 block">Custom Hex</label>
                                <div className="grid grid-cols-2 gap-3">
                                    <ColorPicker 
                                        color={config.custom_config.primary_color}
                                        onChange={(c) => updateCustomConfig("primary_color", c)}
                                        label="Primary"
                                    />
                                    <ColorPicker 
                                        color={config.custom_config.highlight_color}
                                        onChange={(c) => updateCustomConfig("highlight_color", c)}
                                        label="Highlight"
                                    />
                                </div>
                            </div>
                        </motion.div>
                    )}

                        <div className="space-y-2">
                            <label className="text-[10px] font-semibold text-zinc-500 uppercase">Output Format</label>
                            <Select 
                                value={config.resolution} 
                                onValueChange={(v) => updateConfig("resolution", v)}
                                disabled={isProcessing}
                            >
                                <SelectTrigger className="bg-zinc-900/50 border-white/5 h-10">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-zinc-950 border-white/10">
                                    <SelectItem value="1080p">9:16 Vertical (Shorts)</SelectItem>
                                    <SelectItem value="1920x1080">16:9 Landscape (YouTube)</SelectItem>
                                    <SelectItem value="1080x1080">1:1 Square (Instagram)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>


                </section>
                </div>
            </ScrollArea>

            {/* Footer Actions */}
            <div className="p-6 border-t border-white/10 bg-zinc-950/80 backdrop-blur-xl shrink-0 z-10 relative">
                {isProcessing ? (
                    <div className="space-y-3">
                        <div className="flex justify-between text-xs text-zinc-400 font-medium">
                            <span className="animate-pulse text-primary flex items-center"><Wand2 className="w-3 h-3 mr-1 animate-spin" /> Processing...</span>
                            <span className="font-mono">{Math.round(progress)}%</span>
                        </div>
                        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                            <motion.div 
                                className="h-full bg-gradient-to-r from-violet-600 to-indigo-500" 
                                initial={{ width: 0 }}
                                animate={{ width: `${progress}%` }}
                                transition={{ ease: "easeOut" }}
                            />
                        </div>
                        <Button 
                            variant="destructive" 
                            className="w-full h-9 text-xs" 
                            onClick={onCancel}
                        >
                            <XCircle className="h-3 w-3 mr-2" /> Cancel Operation
                        </Button>
                    </div>
                ) : (
                    <Button 
                        variant="cyber"
                        size="xl"
                        className="w-full shadow-[0_0_30px_rgba(124,58,237,0.3)] hover:shadow-[0_0_40px_rgba(124,58,237,0.5)] border-primary/50"
                        onClick={onProcess}
                        disabled={!config.url}
                    >
                        <Sparkles className="h-5 w-5 mr-3 animate-pulse" /> GENERATE CLIPS
                    </Button>
                )}
            </div>
        </motion.div>
    )
}
