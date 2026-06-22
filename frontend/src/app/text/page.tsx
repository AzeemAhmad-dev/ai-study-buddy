"use client";
import { useState, useRef } from "react";

// --- TYPES ---
interface SummaryData {
  summary?: string;
  study_guide?: string;
  keyPoints?: string[];
  executiveSummary?: string;
  key_points?: string[];
  text?: string;
  content?: string;
  [key: string]: any;
}

interface Flashcard {
  front: string;
  back: string;
  question?: string;
  answer?: string;
  [key: string]: any;
}

interface QuizQuestion {
  question: string;
  question_text?: string;
  options: string[];
  correctAnswer: string;
  correct_answer?: string;
  explanation: string;
  [key: string]: any;
}

// --- HELPER COMPONENTS ---

// 1. Native Markdown Parser for the Summary
const FormattedSummary = ({ text }: { text: string }) => {
  if (!text) return <p>No summary available.</p>;

  return (
    <div className="space-y-3 text-gray-300 leading-relaxed">
      {text.split('\n').map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return <br key={i} />;
        
        // Headers
        if (trimmed.startsWith('### ')) return <h3 key={i} className="text-lg font-bold mt-4 text-[#00f3ff]">{trimmed.replace('### ', '')}</h3>;
        if (trimmed.startsWith('## ')) return <h2 key={i} className="text-xl font-bold mt-6 mb-2 text-[#00f3ff] border-b border-white/10 pb-2">{trimmed.replace('## ', '')}</h2>;
        if (trimmed.startsWith('# ')) return <h1 key={i} className="text-2xl font-bold mt-6 mb-4 text-[#00f3ff]">{trimmed.replace('# ', '')}</h1>;
        
        // Lists
        const isListItem = trimmed.startsWith('* ') || trimmed.startsWith('- ');
        const content = isListItem ? trimmed.substring(2) : trimmed;
        
        // Bold Text Parser
        const parts = content.split(/(\*\*.*?\*\*)/);
        const formattedContent = parts.map((part, j) => 
          part.startsWith('**') && part.endsWith('**') 
            ? <strong key={j} className="text-white font-semibold">{part.slice(2, -2)}</strong> 
            : part
        );

        if (isListItem) return <li key={i} className="ml-6 list-disc my-1">{formattedContent}</li>;
        return <p key={i}>{formattedContent}</p>;
      })}
    </div>
  );
};

// 2. Interactive Flashcard Component
const InteractiveFlashcard = ({ card, index }: { card: Flashcard, index: number }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const frontText = card.front || card.question || "Front missing";
  const backText = card.back || card.answer || "Back missing";

  return (
    <div 
      onClick={() => setIsFlipped(!isFlipped)}
      className="relative w-full h-48 cursor-pointer perspective-1000 group"
      style={{ perspective: '1000px' }}
    >
      <div 
        className={`w-full h-full transition-transform duration-500 preserve-3d relative ${isFlipped ? 'rotate-y-180' : ''}`}
        style={{ transformStyle: 'preserve-3d', transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
      >
        {/* Front */}
        <div className="absolute w-full h-full backface-hidden bg-[#121212] border border-white/10 rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-lg hover:border-[#00f3ff]/50 transition-colors" style={{ backfaceVisibility: 'hidden' }}>
          <span className="absolute top-3 left-4 text-[10px] text-[#00f3ff] uppercase tracking-widest font-mono">Card {index + 1}</span>
          <h3 className="text-lg font-medium text-gray-100">{frontText}</h3>
          <span className="absolute bottom-3 text-xs text-gray-500 italic">Click to flip</span>
        </div>
        
        {/* Back */}
        <div className="absolute w-full h-full backface-hidden bg-[#1a1a2e] border border-purple-500/30 rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-lg overflow-y-auto" style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}>
          <p className="text-sm text-gray-200 leading-relaxed">{backText}</p>
        </div>
      </div>
    </div>
  );
};

// 3. Interactive Quiz Component
const InteractiveQuizItem = ({ q, index }: { q: QuizQuestion, index: number }) => {
  const [selectedOpt, setSelectedOpt] = useState<string | null>(null);
  const correctAnswer = q.correct_answer || q.correctAnswer || "";
  const questionText = q.question_text || q.question || "Question missing";

  return (
    <div className="p-6 bg-[#121212] border border-white/10 rounded-xl shadow-lg">
      <div className="flex items-start gap-3 mb-4">
        <span className="shrink-0 text-xs bg-[#00f3ff]/10 text-[#00f3ff] px-2.5 py-1 rounded-full font-mono font-bold mt-0.5">Q-{index + 1}</span>
        <p className="font-medium text-lg text-gray-100">{questionText}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        {(q.options || []).map((opt, i) => {
          const isSelected = selectedOpt === opt;
          const isCorrect = opt === correctAnswer;
          const hasAnswered = selectedOpt !== null;
          
          let btnClass = "p-3 rounded-lg text-sm text-left border transition-all duration-200 ";
          
          if (!hasAnswered) {
            btnClass += "bg-[#1a1a1a] border-white/5 hover:border-[#00f3ff]/50 hover:bg-white/5 cursor-pointer text-gray-300";
          } else {
            btnClass += "cursor-default ";
            if (isCorrect) btnClass += "bg-green-500/20 border-green-500 text-green-100 shadow-[0_0_15px_rgba(34,197,94,0.2)]";
            else if (isSelected && !isCorrect) btnClass += "bg-red-500/20 border-red-500 text-red-100";
            else btnClass += "bg-[#1a1a1a] border-white/5 text-gray-600 opacity-50";
          }

          return (
            <button 
              key={i} 
              disabled={hasAnswered}
              onClick={() => setSelectedOpt(opt)}
              className={btnClass}
            >
              {opt}
            </button>
          );
        })}
      </div>

      {selectedOpt && (
        <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
          <div className={`p-4 rounded-lg border-l-4 ${selectedOpt === correctAnswer ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
            <p className="text-sm text-gray-300">
              <span className="font-bold text-white block mb-1">Explanation:</span>
              {q.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// --- MAIN PAGE ---
export default function TextAnalytics() {
  const [activeTab, setActiveTab] = useState("summary");
  const [inputText, setInputText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gemini-2.5-flash");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [summaryResult, setSummaryResult] = useState<SummaryData | null>(null);
  const [flashcardsResult, setFlashcardsResult] = useState<Flashcard[] | null>(null);
  const [quizResult, setQuizResult] = useState<QuizQuestion[] | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!inputText && !selectedFile) {
      alert("Please provide some text or upload a file to analyze.");
      return;
    }

    if (activeTab === "summary") setSummaryResult(null);
    if (activeTab === "flashcards") setFlashcardsResult(null);
    if (activeTab === "quiz") setQuizResult(null);

    setIsProcessing(true);
    
    const formData = new FormData();
    if (inputText) formData.append("text", inputText);
    if (selectedFile) formData.append("file", selectedFile);
    formData.append("model", selectedModel);

    // FIX: Grab the URL and scrub any accidental trailing slashes
    const rawUrl = process.env.NEXT_PUBLIC_API_URL || "https://ai-study-buddy-vkty.onrender.com";
    const API_BASE_URL = rawUrl.replace(/\/$/, "");

    const endpointMap: Record<string, string> = {
      summary: `${API_BASE_URL}/api/text/summarize`,
      flashcards: `${API_BASE_URL}/api/text/flashcards`,
      quiz: `${API_BASE_URL}/api/text/quiz`
    };

    try {
      const response = await fetch(endpointMap[activeTab], {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(`Server status crash: ${response.status}`);

      const data = await response.json();

      if (activeTab === "summary") {
        setSummaryResult(data);
      } else if (activeTab === "flashcards") {
        setFlashcardsResult(Array.isArray(data) ? data : data.flashcards || data.cards || []);
      } else if (activeTab === "quiz") {
        setQuizResult(Array.isArray(data) ? data : data.questions || data.quiz || []);
      }

    } catch (error) {
      console.error("Execution error:", error);
      alert("Failed to communicate with processing engine.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto text-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 tracking-tight">Text Analytics Engine</h1>
        <p className="text-gray-400">Process documents into structured, interactive study guides.</p>
      </div>

      <div className="mb-10 bg-[#121212] border border-white/5 rounded-xl p-5 shadow-2xl focus-within:border-[#00f3ff]/50 transition-colors">
        <div className="mb-4 border-b border-white/10 pb-5">
          <input type="file" ref={fileInputRef} className="hidden" accept=".pdf,image/png,image/jpeg,image/webp" onChange={handleFileChange} />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/5 rounded-lg text-[#00f3ff]">
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
              </div>
              <span className="text-sm font-medium text-gray-300">{selectedFile ? selectedFile.name : "Attach Syllabus / PDF / Image"}</span>
            </div>
            <div className="flex gap-2">
              {selectedFile && (
                <button onClick={() => setSelectedFile(null)} className="px-4 py-2 text-xs font-semibold text-red-400 bg-red-400/10 hover:bg-red-400/20 rounded-lg transition-colors">Remove</button>
              )}
              <button onClick={() => fileInputRef.current?.click()} className="px-5 py-2 text-xs font-semibold bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors">Browse</button>
            </div>
          </div>
        </div>

        <textarea
          className="w-full h-32 bg-transparent text-gray-200 focus:outline-none resize-none placeholder-gray-600 text-sm leading-relaxed"
          placeholder="...or paste your raw text, lecture notes, or code blocks here."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />
        
        <div className="mt-4 pt-4 border-t border-white/5 flex flex-wrap justify-between items-center gap-4">
          <select 
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-black/50 border border-white/10 text-gray-300 text-sm rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#00f3ff] transition-colors cursor-pointer outline-none"
          >
            <option value="gemini-2.5-flash">Gemini 2.5 Flash (Next-Gen Speed)</option>
            <option value="gemini-1.5-flash-8b-001">Gemini 1.5 Flash-8B (Ultra Fast)</option>
            <option value="gemini-1.5-pro-002">Gemini 1.5 Pro (Deep Reasoning)</option>
          </select>
          <button 
            onClick={handleAnalyze}
            disabled={isProcessing}
            className={`px-8 py-2.5 font-bold text-sm rounded-lg transition-all ${
              isProcessing 
                ? "bg-gray-800 text-gray-500 cursor-not-allowed" 
                : "bg-[#00f3ff] text-black hover:bg-[#00f3ff]/80 hover:shadow-[0_0_20px_rgba(0,243,255,0.4)]"
            }`}
          >
            {isProcessing ? "Processing Data..." : "Analyze Context"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-white/10 mb-8 px-2">
        {["summary", "flashcards", "quiz"].map((tab) => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)} 
            className={`pb-3 text-sm font-semibold capitalize tracking-wide transition-all ${activeTab === tab ? "border-b-2 border-[#00f3ff] text-[#00f3ff]" : "text-gray-500 hover:text-gray-300"}`}
          >
            {tab === "quiz" ? "Quiz Runner" : tab}
          </button>
        ))}
      </div>

      {/* Viewport */}
      <div className="min-h-[400px]">
        {isProcessing && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 animate-in fade-in duration-500">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#00f3ff] mb-6"></div>
            <p className="font-medium tracking-wide">Building your study guide...</p>
            <p className="text-xs mt-2 opacity-50">Tokenizing input material.</p>
          </div>
        )}

        {/* Summary Tab */}
        {!isProcessing && activeTab === "summary" && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {summaryResult ? (
              <div className="bg-[#121212] border border-white/5 rounded-xl p-8 shadow-xl">
                <FormattedSummary text={summaryResult.study_guide || summaryResult.executiveSummary || summaryResult.summary || summaryResult.text || summaryResult.content || ""} />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
                <p className="text-gray-500 font-medium">No document analyzed yet. Submit content above.</p>
              </div>
            )}
          </div>
        )}

        {/* Flashcards Tab */}
        {!isProcessing && activeTab === "flashcards" && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {flashcardsResult && flashcardsResult.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {flashcardsResult.map((card, index) => (
                  <InteractiveFlashcard key={index} card={card} index={index} />
                ))}
              </div>
            ) : (
               <div className="h-64 flex items-center justify-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
                <p className="text-gray-500 font-medium">No flashcards compiled yet.</p>
              </div>
            )}
          </div>
        )}

        {/* Quiz Tab */}
        {!isProcessing && activeTab === "quiz" && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {quizResult && quizResult.length > 0 ? (
              <div className="space-y-6 max-w-4xl mx-auto">
                {quizResult.map((q, index) => (
                  <InteractiveQuizItem key={index} q={q} index={index} />
                ))}
              </div>
            ) : (
               <div className="h-64 flex items-center justify-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
                <p className="text-gray-500 font-medium">No evaluation questions generated yet.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}