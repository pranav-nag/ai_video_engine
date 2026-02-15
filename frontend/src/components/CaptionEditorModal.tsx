import { useState, useRef, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Loader2, Save, RotateCcw, MonitorPlay, MousePointer2 } from "lucide-react"

interface CaptionEditorModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    clipPath: string
    clipTitle: string
    onSave: (newConfig: any) => Promise<void>
}

export function CaptionEditorModal({ open, onOpenChange, clipPath, clipTitle, onSave }: CaptionEditorModalProps) {
    const [isSaving, setIsSaving] = useState(false)
    const [marginTop, setMarginTop] = useState(20) // Default % from bottom
    const videoRef = useRef<HTMLVideoElement>(null)

    // Convert local file path to URL
    // Electron usually handles this, or we serve via backend static
    // Assuming backend serves output files at http://localhost:8000/output/...
    // BUT clipPath is full absolute path "e:\..."
    // We might need a helper to convert to local file URL if allowed, or serve statically.
    // For now, let's assume valid URL or blob. 
    // Actually, Electron can load local files with `file://` protocol if security allows.
    const videoSrc = clipPath.startsWith("http") ? clipPath : `file:///${clipPath.replace(/\\/g, "/")}`

    const handleSave = async () => {
        setIsSaving(true)
        try {
            // We only send the margin logic for now
            // margin_v is usually pixels in ASS, but we might want %
            // Let's send a custom_config that renderer understands
            await onSave({
               margin_v: marginTop // we will interpret this as % from bottom or pixels
            })
            onOpenChange(false)
        } catch (e) {
            console.error(e)
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[400px] bg-black/95 border-zinc-800 text-white p-0 overflow-hidden gap-0">
                <DialogHeader className="p-4 bg-zinc-900 border-b border-zinc-800">
                    <DialogTitle className="text-sm font-medium flex items-center">
                        <MousePointer2 className="w-4 h-4 mr-2 text-purple-400" />
                        Edit Captions: {clipTitle}
                    </DialogTitle>
                </DialogHeader>

                <div className="relative aspect-[9/16] bg-zinc-950 flex justify-center overflow-hidden group">
                    {/* Video Player */}
                    <video 
                        ref={videoRef}
                        src={videoSrc}
                        className="h-full w-full object-cover opacity-80"
                        autoPlay
                        loop
                        muted
                        controls={false}
                    />

                    {/* Drag Overlay (Simplified as Slider for v1) */}
                    {/* Implementing draggable box over video is complex for v1. 
                        Let's use a visual slider overlay that moves a "safe zone" box. */}
                    
                    <div 
                        className="absolute left-4 right-4 border-2 border-dashed border-green-500/50 bg-green-500/10 flex items-center justify-center pointer-events-none transition-all duration-200"
                        style={{ bottom: `${marginTop}%`, height: "15%" }}
                    >
                        <span className="text-xs font-bold text-green-400 bg-black/50 px-2 py-1 rounded">CAPTION ZONE</span>
                    </div>

                    {/* Controls Overlay */}
                    <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/90 to-transparent">
                        <Label className="text-xs text-zinc-400 mb-2 block">Vertical Position</Label>
                        <div className="flex items-center space-x-4">
                            <MonitorPlay className="w-4 h-4 text-zinc-500" />
                            <Slider 
                                value={[marginTop]} 
                                min={5} 
                                max={90} 
                                step={1}
                                onValueChange={(val) => setMarginTop(val[0])}
                                className="flex-1"
                            />
                            <span className="text-xs font-mono text-zinc-300 w-8 text-right">{marginTop}%</span>
                        </div>
                    </div>
                </div>

                <DialogFooter className="p-4 bg-zinc-900 border-t border-zinc-800">
                    <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)} disabled={isSaving}>
                        Cancel
                    </Button>
                    <Button size="sm" onClick={handleSave} disabled={isSaving} className="bg-purple-600 hover:bg-purple-700 text-white">
                        {isSaving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                        Re-Render
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
