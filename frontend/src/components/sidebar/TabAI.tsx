import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScrollArea } from "@/components/ui/scroll-area" // Added import
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { BrainCircuit, ScanFace, Tv2, Gamepad2, Mic2, Lightbulb, Clapperboard, Split } from "lucide-react"
import { VideoConfig } from "../../App"

interface TabAIProps {
    config: VideoConfig
    setConfig: React.Dispatch<React.SetStateAction<VideoConfig>>
    isProcessing: boolean
}

export function TabAI({ config, setConfig, isProcessing }: TabAIProps) {

    const updateConfig = (key: keyof VideoConfig, value: any) => {
        setConfig(prev => ({ ...prev, [key]: value }))
    }

    return (
        <ScrollArea className="h-full">
            <div className="space-y-8 p-6 pb-32">
                {/* Strategy Header */}
                <div className="flex items-center space-x-2 mb-6">
                    <div className="h-8 w-8 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                         <BrainCircuit className="w-4 h-4 text-purple-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-zinc-100 tracking-tight">AI Strategy</h3>
                        <p className="text-[10px] text-zinc-500 font-medium">Configure how the Engine "thinks"</p>
                    </div>
                </div>

                {/* Content Genre */}
                <div className="space-y-3">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase ml-1">Content Genre</label>
                    <div className="grid grid-cols-2 gap-3">
                        {[
                            { id: "General", icon: Tv2, label: "General" },
                            { id: "Podcast", icon: Mic2, label: "Podcast" },
                            { id: "Motivational", icon: Lightbulb, label: "Motivation" },
                            { id: "Gaming", icon: Gamepad2, label: "Gaming" },
                        ].map((genre) => (
                            <div 
                                key={genre.id}
                                onClick={() => !isProcessing && updateConfig("content_type", genre.id)}
                                className={`
                                    cursor-pointer group relative p-3 rounded-xl border transition-all duration-200
                                    ${config.content_type === genre.id 
                                        ? "bg-purple-500/10 border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.15)]" 
                                        : "bg-zinc-900/30 border-white/5 hover:bg-zinc-800/50 hover:border-white/10"}
                                `}
                            >
                                <div className="flex items-center space-x-3">
                                    <genre.icon className={`w-4 h-4 ${config.content_type === genre.id ? "text-purple-400" : "text-zinc-500 group-hover:text-zinc-300"}`} />
                                    <span className={`text-xs font-medium ${config.content_type === genre.id ? "text-white" : "text-zinc-400 group-hover:text-zinc-200"}`}>
                                        {genre.label}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Focus Mode */}
                <div className="space-y-3">
                     <label className="text-[10px] font-bold text-zinc-500 uppercase ml-1">Visual Focus</label>
                     <Select 
                        value={config.focus_mode} 
                        onValueChange={(v) => updateConfig("focus_mode", v)}
                        disabled={isProcessing}
                    >
                        <SelectTrigger className="bg-zinc-900/50 border-white/5 h-11">
                            <div className="flex items-center">
                                <ScanFace className="w-4 h-4 mr-2 text-zinc-400" />
                                <SelectValue />
                            </div>
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-950 border-white/10">
                            <SelectItem value="center">Center Crop (Static)</SelectItem>
                            <SelectItem value="auto-face">Auto-Face Detection (Dynamic)</SelectItem>
                            <SelectItem value="left">Left Third</SelectItem>
                            <SelectItem value="right">Right Third</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Duration Strategy */}
                <div className="space-y-3 p-4 bg-zinc-900/30 rounded-xl border border-white/5">
                    <div className="flex justify-between items-center mb-2">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase">Target Duration</label>
                         <Badge variant="outline" className="bg-purple-500/10 text-purple-300 border-purple-500/20 py-0 h-5 font-mono text-[10px]">
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
                    
                    <div className="flex justify-between text-[10px] text-zinc-600 font-medium px-1">
                        <span>Short Bursts</span>
                        <span>Story Mode</span>
                    </div>
                </div>
                
                {/* Advanced Visuals */}
                <div className="space-y-4 pt-4 border-t border-white/5">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase ml-1">Composition Rules</label>
                    
                    <div className="bg-zinc-900/30 rounded-xl border border-white/5 overflow-hidden">
                        {/* B-Roll Toggle */}
                        <div className="flex items-center justify-between p-3 border-b border-white/5 hover:bg-white/5 transition-colors">
                            <div className="flex items-center space-x-3">
                                <div className={`p-1.5 rounded-lg ${config.use_b_roll ? "bg-purple-500/20 text-purple-400" : "bg-zinc-800 text-zinc-500"}`}>
                                    <Clapperboard className="w-4 h-4" />
                                </div>
                                <div className="space-y-0.5">
                                    <Label className="text-sm font-medium text-zinc-200">Smart B-Roll</Label>
                                    <p className="text-[10px] text-zinc-500">Auto-insert stock footage for keywords</p>
                                </div>
                            </div>
                            <Switch
                                checked={config.use_b_roll}
                                onCheckedChange={(c) => updateConfig("use_b_roll", c)}
                                disabled={isProcessing}
                            />
                        </div>

                        {/* Split-Screen Toggle */}
                        <div className="flex items-center justify-between p-3 hover:bg-white/5 transition-colors">
                            <div className="flex items-center space-x-3">
                                <div className={`p-1.5 rounded-lg ${config.use_split_screen ? "bg-blue-500/20 text-blue-400" : "bg-zinc-800 text-zinc-500"}`}>
                                    <Split className="w-4 h-4" />
                                </div>
                                <div className="space-y-0.5">
                                    <Label className="text-sm font-medium text-zinc-200">Video Podcast</Label>
                                    <p className="text-[10px] text-zinc-500">Auto-detect & crop 2 speakers</p>
                                </div>
                            </div>
                             <Switch
                                checked={config.use_split_screen}
                                onCheckedChange={(c) => updateConfig("use_split_screen", c)}
                                disabled={isProcessing}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </ScrollArea>
    )
}
