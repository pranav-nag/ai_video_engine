import { useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Play, Share2, MoreVertical, Film, Sparkles, Download, Edit2 } from "lucide-react"
import { motion } from "framer-motion"
import { Button } from "./ui/button"
import { CaptionEditorModal } from "./CaptionEditorModal"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface Clip {
    filename: string
    path: string
    thumbnail?: string
    score?: number
    source_path?: string
    start_time?: number
    end_time?: number
}

const ipcRenderer = (window as any).require ? (window as any).require('electron').ipcRenderer : { 
    send: () => console.warn("Electron IPC not available") 
};

export function VideoComposer({ clips }: { clips: Clip[] }) {
    const handlePlay = (path: string) => {
        ipcRenderer.send('open-file', path);
    }

    const [editingClip, setEditingClip] = useState<Clip | null>(null)

    const handleRerender = async (newConfig: any) => {
        if (!editingClip) return
        
        // Call backend rerender endpoint
        try {
            await fetch("http://127.0.0.1:8000/rerender_clip", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    path: editingClip.path,
                    custom_config: newConfig
                })
            })
            // We might want to show a toast or optimistically update UI
            // Ideally backend sends a new "clip_ready" event when done
        } catch (e) {
            console.error(e)
        }
    }

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    }

    const item = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 }
    }

    if (clips.length === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center min-h-[500px] text-zinc-500 space-y-6">
                <motion.div 
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5 }}
                    className="relative"
                >
                    <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl animate-pulse"></div>
                    <div className="h-32 w-32 rounded-3xl bg-zinc-900/50 backdrop-blur-xl flex items-center justify-center border border-white/10 shadow-2xl relative z-10">
                        <Film className="h-12 w-12 text-zinc-700" />
                    </div>
                    {/* Floating Icons */}
                    <motion.div 
                        animate={{ y: [0, -10, 0] }} 
                        transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                        className="absolute -top-4 -right-4 bg-zinc-800 p-2 rounded-lg border border-white/5 shadow-lg z-20"
                    >
                        <Sparkles className="h-5 w-5 text-yellow-500" />
                    </motion.div>
                </motion.div>
                
                <div className="text-center space-y-2">
                    <h3 className="text-2xl font-bold text-white tracking-tight">Creative Stage</h3>
                    <p className="text-sm text-zinc-500 max-w-xs mx-auto">
                        Your AI-generated masterpieces will appear here. 
                        Paste a URL to begin the magic.
                    </p>
                </div>
            </div>
        )
    }

    return (
        <ScrollArea className="flex-1 h-full">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight flex items-center">
                        <Sparkles className="w-5 h-5 mr-3 text-primary animate-pulse" />
                        Generated Content
                    </h2>
                    <p className="text-sm text-zinc-500 mt-1 ml-8">Your viral clips differ from the competition.</p>
                </div>
                <div className="bg-zinc-900/50 px-3 py-1 rounded-full border border-white/5 text-xs text-zinc-400 font-mono">
                    {clips.length} RESULTS
                </div>
            </div>
            
            <motion.div 
                variants={container}
                initial="hidden"
                animate="show"
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20"
            >
                {clips.map((clip, i) => (
                    <motion.div 
                        key={i} 
                        variants={item}
                        className="group relative bg-zinc-900/40 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/5 hover:border-primary/50 hover:shadow-[0_0_30px_rgba(124,58,237,0.15)] transition-all duration-500 cursor-pointer"
                        onClick={() => handlePlay(clip.path)}
                    >
                        {/* Thumbnail Area */}
                        <div className="aspect-[9/16] bg-black2 relative overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent opacity-80 z-10"></div>
                            
                            {/* Thumbnail or Gradient */}
                            {clip.thumbnail ? (
                                <img 
                                    src={`file://${clip.thumbnail.replace(/\\/g, "/")}`} 
                                    alt={clip.filename}
                                    className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                                />
                            ) : (
                                <div className="absolute inset-0 bg-gradient-to-br from-zinc-800 to-zinc-950 group-hover:scale-110 transition-transform duration-700"></div>
                            )}

                            {/* Play Button Overlay */}
                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-20">
                                <div className="h-14 w-14 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center border border-white/20 shadow-xl transform scale-50 group-hover:scale-100 transition-all duration-300 hover:bg-white/20">
                                    <Play className="h-6 w-6 text-white ml-1 fill-white" />
                                </div>
                            </div>

                            {/* Badges */}
                            <div className="absolute top-3 right-3 flex flex-col gap-2 items-end z-20">
                                <div className="px-2 py-1 bg-black/40 backdrop-blur-md border border-white/10 rounded-md text-[10px] text-zinc-200 font-bold uppercase tracking-widest shadow-lg">
                                    VIRAL
                                </div>
                                {clip.score !== undefined && clip.score > 0 && (
                                    <TooltipProvider>
                                        <Tooltip delayDuration={0}>
                                            <TooltipTrigger asChild>
                                                <div className={`px-2 py-1 backdrop-blur-md border border-white/10 rounded-md text-[10px] font-bold uppercase tracking-widest shadow-lg flex items-center cursor-help ${
                                                    clip.score >= 85 ? "bg-green-500/20 text-green-300" :
                                                    clip.score >= 70 ? "bg-yellow-500/20 text-yellow-300" :
                                                    "bg-red-500/20 text-red-300"
                                                }`}>
                                                    <Sparkles className="w-3 h-3 mr-1" />
                                                    {Math.round(clip.score)}%
                                                </div>
                                            </TooltipTrigger>
                                            <TooltipContent side="left" className="bg-zinc-950 border-white/10 text-white text-xs">
                                                <p>Viral Probability: {Math.round(clip.score)}%</p>
                                                <p className="text-[10px] text-zinc-400 font-normal normal-case tracking-normal">Estimated chance of going viral on social media.</p>
                                            </TooltipContent>
                                        </Tooltip>
                                    </TooltipProvider>
                                )}
                            </div>
                        </div>
                        
                        {/* Content Info */}
                        <div className="absolute bottom-0 left-0 right-0 p-5 z-20 translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
                            <h4 className="font-bold text-sm text-white line-clamp-1 mb-2 drop-shadow-lg" title={clip.filename}>
                                {clip.filename}
                            </h4>
                            <div className="flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75">
                                <span className="text-[10px] text-zinc-300 font-mono bg-white/5 border border-white/5 px-2 py-1 rounded-md">1080P • 60FPS</span>
                                <div className="flex space-x-2">
                                    <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/10 text-white/70 hover:text-white" onClick={() => handlePlay(clip.path)}>
                                        <Play className="w-4 h-4 fill-current" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/10 text-white/70 hover:text-white" onClick={() => setEditingClip(clip)}>
                                        <Edit2 className="w-4 h-4" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/10 text-white/70 hover:text-white">
                                        <Share2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </motion.div>

            {editingClip && (
                <CaptionEditorModal 
                    open={!!editingClip} 
                    onOpenChange={(open) => !open && setEditingClip(null)} 
                    clipPath={editingClip.path}
                    clipTitle={editingClip.filename}
                    onSave={handleRerender}
                />
            )}
        </ScrollArea>
    )
}
