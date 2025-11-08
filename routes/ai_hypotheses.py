import {useEffect
        import useState} from "react"
import axios from "axios"
/* eslint-disable @ typescript-eslint/no-explicit-any * /
"use client"


interface Hypothesis {
    id: string
    title: string
    summary: string
    confidence: number
    mechanisms: string[]
    biomarkers: string[]
    citations: string[]
    source?: string
    created_at?: string
}

export default function AIHypothesesPage() {
    const[data, setData] = useState < Hypothesis[] > ([])
    const[loading, setLoading] = useState(true)
    const[error, setError] = useState < string | null > (null)
    const[filterMechanism, setFilterMechanism] = useState("")
    const[minConfidence, setMinConfidence] = useState(0)

    useEffect(()=> {
        const fetchData= async () = > {
            try {
              const res= await axios.get(
                  `${process.env.NEXT_PUBLIC_API_URL}/ai/hypotheses`
              )
              console.log("Fetched data:", res.data)
              setData(res.data)
              } catch(err: any) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    const timeSince = (dateString: string | undefined) = > {
        if (!dateString) return null
        const created = new Date(dateString).getTime()
        const diffMs = Date.now() - created
        const diffHrs = Math.floor(diffMs / (1000 * 60 * 60))
        if (diffHrs < 1) {
            const mins = Math.floor(diffMs / (1000 * 60))
            return `${mins}m ago`
        }
        if (diffHrs < 24) return `${diffHrs}h ago`
        const days = Math.floor(diffHrs / 24)
        return `${days}d ago`
    }

    if (loading) return < p className = "p-6 text-gray-500" > Loading hypotheses… < /p >
    if (error)
    return < p className = "p-6 text-red-600" > Error loading data: {error} < /p >

    const filtered = data.filter((h)=> {
        const mechMatch =
        !filterMechanism | | h.mechanisms?.includes(filterMechanism)
        const confMatch= h.confidence >= minConfidence
        return mechMatch & & confMatch
    })

    return (
        < div className="max-w-5xl mx-auto px-6 pb-12" >
        < h1 className="text-3xl font-semibold text-center mt-2 mb-2" >
        AI-Generated Hypotheses
        < /h1 >
        < p className="text-gray-600 text-center mb-8 max-w-2xl mx-auto" >
        Machine-generated causal links discovered from ME/CFS research data —
        synthesized by AI from biomarkers, mechanisms, and study evidence.
        < /p >

        {/* Filters * /}
        < div className="flex flex-col sm:flex-row items-center gap-4 mb-8 justify-center bg-gray-50 p-4 rounded-xl shadow-sm border border-gray-100" >
        < div className="flex items-center gap-2" >
        < label className="text-sm text-gray-700 font-medium" >
        Mechanism:
        < /label >
        < select
        value={filterMechanism}
        onChange={(e)= > setFilterMechanism(e.target.value)}
        className="border rounded-lg p-2 bg-white text-gray-800"
        >
        <option value="" > All Mechanisms < /option >
        < option value="vascular" > Vascular < /option >
        < option value="immune" > Immune < /option >
        < option value="mitochondrial" > Mitochondrial < /option >
        < option value="neuroinflammatory" > Neuroinflammatory < /option >
        < / select >
        < / div >

        < div className="flex items-center gap-2" >
        < label className="text-sm text-gray-700 font-medium" >
        Confidence:
        < /label >
        < input
        type="range"
        min={0}
        max={1}
        step={0.1}
        value={minConfidence}
        onChange={(e)= > setMinConfidence(Number(e.target.value))}
        className="w-32 cursor-pointer"
        / >
        < span className="text-sm text-gray-600" >
        ≥ {(minConfidence * 100).toFixed(0)} %
        </span >
        < / div >

        < div className="flex gap-2" >
        < button
        onClick={()= > window.location.reload()}
        className="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm shadow hover:bg-blue-600 transition cursor-pointer"
        >
        Refresh
        < /button >
        < button
        onClick={()= > {
            navigator.clipboard.writeText(window.location.href)
            alert("Link copied!")
        }}
        className="bg-gray-100 border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 transition cursor-pointer"
        >
        Share Link
        < /button >
        < / div >
        < / div >

        {/* Hypothesis cards * /}
        < div className="grid gap-6" >
        {filtered.map((h)= > (
            < div
            key={h.id}
            className="bg-white rounded-2xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition"
            >
            <div className="flex justify-between items-start mb-2" >
            < h2 className="text-xl font-medium" > {h.title} < /h2 >
            {h.source === "AI" & & (
                < span className="text-xs bg-blue-50 text-blue-600 font-medium px-2 py-1 rounded-full" >
                Generated by AI {h.created_at & & `• ${timeSince(h.created_at)}`}
                < /span >
            )}
            < /div >

            < p className="text-gray-700 mb-3" > {h.summary} < /p >

            < div className="flex items-center gap-2 mb-2" >
            < span className="text-sm font-medium" > Confidence: < /span >
            < div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden" >
            < div
            className="bg-green-500 h-2"
            style={{width: `${h.confidence * 100} % `}}
            > </div >
            < / div >
            < span className="text-sm" >
            {(h.confidence * 100).toFixed(0)} %
            </span >
            < / div >

            < div className="flex flex-wrap gap-2 mb-2" >
            {h.mechanisms?.map((m)=> (
                < span
                key={m}
                className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs"
                >
                {m}
                < /span >
            ))}
            {h.biomarkers?.map((b)=> (
                < span
                key={b}
                className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs"
                >
                {b}
                < /span >
            ))}
            < /div >

            < div className="text-xs text-gray-500 mt-2" >
            Cited in: {h.citations?.join(", ") | | "—"}
            < /div >
            < / div >
        ))}
        < /div >

        {filtered.length === 0 & & (
            < p className="text-gray-500 text-center mt-8" >
            No hypotheses match your filters.
            < /p >
        )}
        < /div >
    )
}
