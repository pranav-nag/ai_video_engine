import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScrollArea } from "@/components/ui/scroll-area" // Added import
import { Download, MonitorPlay, Timer, Sparkles, Wand2, Scissors } from "lucide-react"
import { motion } from "framer-motion"
import { VideoConfig } from "../../App"

interface TabMediaProps {
    config: VideoConfig
    setConfig: React.Dispatch<React.SetStateAction<VideoConfig>>
    onFetchMetadata: () => void
    isFetchingMetadata: boolean
    isProcessing: boolean
    videoMetadata: { title: string; duration: number } | null
}

export function TabMedia({ 
    config, 
    setConfig, 
    onFetchMetadata, 
    isFetchingMetadata, 
    isProcessing,
    videoMetadata 
}: TabMediaProps) {

    const updateConfig = (key: keyof VideoConfig, value: any) => {
        setConfig(prev => ({ ...prev, [key]: value }))
    }

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60)
        const s = Math.floor(seconds % 60)
        return `${m}:${s < 10 ? '0' : ''}${s}`
    }

    return (
        <ScrollArea className="h-full">
            <div className="space-y-6 p-6 pb-32">
                {/* URL Input Group */}
                <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                        <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                             <Download className="w-3 h-3 text-primary" />
                        </div>
                        <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Source Media</h3>
                    </div>
                    
                    <div className="p-1 bg-zinc-900/50 rounded-xl border border-white/5 shadow-sm group hover:border-white/10 transition-colors">
                        <div className="flex space-x-2 p-2">
                            <Input 
                                placeholder="Paste YouTube URL..." 
                                className="bg-zinc-950/50 border-white/10 focus:ring-primary/50 text-sm h-10 shadow-inner"
                                value={config.url}
                                onChange={(e) => updateConfig("url", e.target.value)}
                                disabled={isProcessing}
                            />
                            <Button 
                                className="bg-zinc-800 hover:bg-zinc-700 data-[active=true]:bg-primary h-10 w-12 shadow-lg"
                                onClick={onFetchMetadata}
                                disabled={!config.url || isProcessing || isFetchingMetadata}
                                data-active={isFetchingMetadata}
                            >
                                {isFetchingMetadata ? <Wand2 className="w-4 h-4 animate-spin text-white" /> : <Sparkles className="w-4 h-4 text-primary" />}
                            </Button>
                        </div>

                        {videoMetadata && (
                            <motion.div 
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                className="px-3 pb-3"
                            >
                                <div className="p-3 bg-gradient-to-r from-primary/10 to-transparent rounded-lg border border-primary/10 space-y-1">
                                    <div className="text-zinc-100 font-medium truncate text-xs flex items-center">
                                        <MonitorPlay className="w-3.5 h-3.5 mr-2 text-primary" />
                                        {videoMetadata.title}
                                    </div>
                                    <div className="text-zinc-400 text-[10px] pl-5 flex items-center font-mono">
                                        <Timer className="w-3 h-3 mr-1.5" />
                                        {formatTime(videoMetadata.duration)}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </div>
                </div>

                {/* Trimming Section */}
                <div className="space-y-3">
                     <div className="flex items-center space-x-2">
                        <div className="h-6 w-6 rounded-full bg-orange-500/10 flex items-center justify-center">
                             <Scissors className="w-3 h-3 text-orange-500" />
                        </div>
                        <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Trim & Cut</h3>
                    </div>

                    <div className="p-4 bg-zinc-900/30 rounded-xl border border-white/5 space-y-5">
                        {/* Time Display */}
                        <div className="flex items-center justify-between gap-3 bg-zinc-950/50 p-2 rounded-lg border border-white/5">
                             <div className="text-center w-full">
                                <span className="text-[10px] text-zinc-500 uppercase font-bold block mb-1">Start</span>
                                <span className="text-xs font-mono text-white">{formatTime(parseInt(config.start_time) || 0)}</span>
                             </div>
                             <div className="h-8 w-[1px] bg-white/10" />
                             <div className="text-center w-full">
                                <span className="text-[10px] text-zinc-500 uppercase font-bold block mb-1">End</span>
                                <span className="text-xs font-mono text-white">
                                    {videoMetadata ? formatTime(parseInt(config.end_time) || videoMetadata.duration) : "Full Video"}
                                </span>
                             </div>
                        </div>

                        {/* Slider */}
                        <div className="pt-2 px-1">
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

                        {/* Quick Filters */}
                        <div className="grid grid-cols-3 gap-2">
                            {[
                                { 
                                    label: "Full Video", 
                                    action: () => videoMetadata && setConfig(prev => ({ ...prev, start_time: "0", end_time: videoMetadata.duration.toString() })),
                                    isActive: videoMetadata && config.start_time === "0" && config.end_time === videoMetadata.duration.toString()
                                },
                                { 
                                    label: "First 10m", 
                                    action: () => setConfig(prev => ({ ...prev, start_time: "0", end_time: "600" })),
                                    isActive: config.start_time === "0" && config.end_time === "600"
                                },
                                { 
                                    label: "Last 10m", 
                                    action: () => videoMetadata && setConfig(prev => ({ ...prev, start_time: Math.max(0, videoMetadata.duration - 600).toString(), end_time: videoMetadata.duration.toString() })),
                                    isActive: videoMetadata && config.start_time === Math.max(0, videoMetadata.duration - 600).toString() && config.end_time === videoMetadata.duration.toString()
                                }
                            ].map((btn) => (
                                <Badge 
                                    key={btn.label}
                                    variant={btn.isActive ? "default" : "outline"}
                                    className={`
                                        justify-center cursor-pointer h-8 text-[10px] transition-all
                                        ${btn.isActive 
                                            ? "bg-primary text-white border-primary shadow-[0_0_10px_rgba(124,58,237,0.3)]" 
                                            : "hover:bg-white/10 hover:text-white hover:border-white/20 text-zinc-500"}
                                    `}
                                    onClick={btn.action}
                                >
                                    {btn.label}
                                </Badge>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Output Format */}
                <div className="space-y-2">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase ml-1">Aspect Ratio</label>
                    <Select 
                        value={config.resolution} 
                        onValueChange={(v) => updateConfig("resolution", v)}
                        disabled={isProcessing}
                    >
                        <SelectTrigger className="bg-zinc-900/50 border-white/5 h-11">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-950 border-white/10">
                            <SelectItem value="1080p">9:16 Vertical (Shorts/TikTok)</SelectItem>
                            <SelectItem value="1920x1080">16:9 Landscape (YouTube)</SelectItem>
                            <SelectItem value="1080x1080">1:1 Square (Instagram/LinkedIn)</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>
        </ScrollArea>
    )
}
