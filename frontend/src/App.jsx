import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  Search, 
  Building, 
  ArrowLeft, 
  Upload, 
  Check, 
  AlertTriangle, 
  ShieldCheck, 
  Moon, 
  Sun, 
  Layers, 
  Info,
  Calendar,
  Users,
  MessageSquare,
  Activity,
  Award,
  ChevronDown,
  ChevronRight,
  Plus,
  Settings,
  Database,
  Mail,
  Lock,
  LogOut
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  Legend,
  Cell
} from 'recharts'
import './App.css'

const API_BASE = "http://127.0.0.1:8000"

function App() {
  // Authentication State
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  // Navigation: 'portfolio' | 'detail' | 'batch' | 'metrics'
  const [view, setView] = useState('portfolio')
  const [selectedBusinessId, setSelectedBusinessId] = useState(null)
  
  // Data State
  const [businesses, setBusinesses] = useState([])
  const [selectedBusiness, setSelectedBusiness] = useState(null)
  const [loading, setLoading] = useState(false)
  const [portfolioLoading, setPortfolioLoading] = useState(true)
  
  // UI State
  const [darkMode, setDarkMode] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('All')
  const [cityFilter, setCityFilter] = useState('All')
  const [riskFilter, setRiskFilter] = useState('All')
  const [sortBy, setSortBy] = useState('score_desc')
  
  // Detail Page Active Tab: 'transactions' | 'social' | 'reviews' | 'comparison'
  const [activeDetailTab, setActiveDetailTab] = useState('transactions')
  
  // Batch Score State
  const [batchFile, setBatchFile] = useState(null)
  const [batchUploading, setBatchUploading] = useState(false)
  const [batchResults, setBatchResults] = useState(null)

  // Toggle Dark Mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  // Load Portfolio Businesses on Mount
  useEffect(() => {
    fetchPortfolio()
  }, [])

  const fetchPortfolio = async () => {
    setPortfolioLoading(true)
    try {
      const res = await fetch(`${API_BASE}/businesses`)
      if (res.ok) {
        const data = await res.json()
        setBusinesses(data)
      } else {
        console.error("Failed to load portfolio")
      }
    } catch (e) {
      console.error("Error fetching portfolio:", e)
    } finally {
      setPortfolioLoading(false)
    }
  }

  // Handle Login Authentication
  const handleLoginSubmit = (e) => {
    e.preventDefault()
    if (username === 'analyst@alternatrust.com' && password === 'admin123') {
      setIsLoggedIn(true)
      setLoginError('')
    } else {
      setLoginError('Invalid username or password. Please try again.')
    }
  }

  // Load Single Business History & Details
  const handleViewDetails = async (businessId) => {
    setSelectedBusinessId(businessId)
    setView('detail')
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/business/${businessId}/history`)
      if (res.ok) {
        const data = await res.json()
        setSelectedBusiness(data)
      } else {
        console.error("Failed to load business details")
      }
    } catch (e) {
      console.error("Error loading business details:", e)
    } finally {
      setLoading(false)
    }
  }

  // Handle Batch File Upload
  const handleFileDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer?.files[0] || e.target.files[0]
    if (file && file.name.endsWith('.csv')) {
      setBatchFile(file)
    } else {
      alert("Please upload a valid CSV file.")
    }
  }

  const handleUploadBatch = async () => {
    if (!batchFile) return
    setBatchUploading(true)
    const formData = new FormData()
    formData.append("file", batchFile)
    
    try {
      const res = await fetch(`${API_BASE}/batch-score`, {
        method: "POST",
        body: formData
      })
      if (res.ok) {
        const data = await res.json()
        setBatchResults(data)
      } else {
        const err = await res.json()
        alert(`Failed to upload batch: ${err.detail || "Error"}`)
      }
    } catch (e) {
      console.error("Error uploading batch:", e)
      alert("Error contacting the scoring backend server.")
    } finally {
      setBatchUploading(false)
    }
  }

  // Sort and Filter logic for Portfolio Page
  const getFilteredBusinesses = () => {
    return businesses
      .filter(b => {
        const matchesSearch = b.business_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                              b.owner_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                              b.business_id.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesCategory = categoryFilter === 'All' || b.category === categoryFilter
        const matchesCity = cityFilter === 'All' || b.city === cityFilter
        const matchesRisk = riskFilter === 'All' || b.risk_tier === riskFilter
        return matchesSearch && matchesCategory && matchesCity && matchesRisk
      })
      .sort((a, b) => {
        if (sortBy === 'score_desc') return b.credit_score - a.credit_score
        if (sortBy === 'score_asc') return a.credit_score - b.credit_score
        if (sortBy === 'name') return a.business_name.localeCompare(b.business_name)
        if (sortBy === 'years') return (b.years_in_operation || 0) - (a.years_in_operation || 0)
        return 0
      })
  }

  const filteredBiz = getFilteredBusinesses()

  // Calculate peer stats for comparison tab
  const getPeerAverages = () => {
    if (!selectedBusiness || businesses.length === 0) return null
    const category = selectedBusiness.metadata.category
    const peers = businesses.filter(b => b.category === category)
    
    const avgScore = peers.reduce((acc, p) => acc + p.credit_score, 0) / peers.length
    const avgYears = peers.reduce((acc, p) => acc + (p.years_in_operation || 0), 0) / peers.length
    
    return {
      score: roundToDecimal(avgScore, 1),
      years: roundToDecimal(avgYears, 1)
    }
  }

  const roundToDecimal = (num, decimals) => {
    return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals)
  }

  // Formulate Actionable Recommendations from SHAP features
  const getActionableRecommendations = (topFactors) => {
    const recommendations = []
    topFactors.forEach(factor => {
      if (factor.impact === 'negative') {
        const feat = factor.feature
        if (feat === 'upi_vol_cv') {
          recommendations.push({
            title: "Improve Deposit Consistency",
            text: "Your weekly transaction deposits show high variance. Standardizing cash flow deposits week-over-week will boost this score.",
            action: "Deposit cash daily into UPI account"
          })
        } else if (feat === 'review_sentiment_mean') {
          recommendations.push({
            title: "Enhance Review Quality",
            text: "Sentiment in customer reviews is low or declining. Boost reviews by engaging customers directly to resolve problems.",
            action: "Respond to customer reviews promptly"
          })
        } else if (feat === 'upi_momentum') {
          recommendations.push({
            title: "Rebuild Transaction Volume Momentum",
            text: "Sales in the last 12 weeks are lower compared to the rest of the year. Consider launching marketing promos to boost volume.",
            action: "Run weekend customer discounts"
          })
        } else if (feat === 'social_engagement_mean' || feat === 'social_posts_mean') {
          recommendations.push({
            title: "Boost Digital Presence",
            text: "Infrequent posting or low social media engagement is drag on your score. Engage your community with regular posts.",
            action: "Post weekly social updates"
          })
        } else if (feat === 'footfall_peak_ratio') {
          recommendations.push({
            title: "Optimize Peak Business Times",
            text: "Merchant check-ins during popular hours are low. Boost check-ins during peak evening slots with targeted happy hour activities.",
            action: "Host peak-hours promotional events"
          })
        } else if (feat.startsWith('tfidf_')) {
          const keyword = fontCleanTfidf(feat)
          recommendations.push({
            title: `Address Complaints about: '${keyword.toUpperCase()}'`,
            text: `High frequency of word '${keyword}' in text reviews signals underlying issues. Audit operations to resolve customer dissatisfaction.`,
            action: `Train staff on '${keyword}' related workflows`
          })
        }
      }
    })
    
    // Add default if no negative factors
    if (recommendations.length === 0) {
      recommendations.push({
        title: "Maintain Solid Performance",
        text: "Your alternative credit metrics are strong. Keep transaction volumes steady and ratings high to maintain credit status.",
        action: "No corrective actions required"
      })
    }
    
    return recommendations
  }

  const fontCleanTfidf = (featName) => {
    return featName.replace('tfidf_', '')
  }

  // Get color schemes based on risk tier
  const getRiskColor = (tier) => {
    if (tier === 'Low Risk') return { bg: 'bg-emerald-50 dark:bg-emerald-950/30', text: 'text-emerald-700 dark:text-emerald-400', border: 'border-emerald-200 dark:border-emerald-800/40', label: 'Low Risk' }
    if (tier === 'Medium Risk') return { bg: 'bg-amber-50 dark:bg-amber-950/30', text: 'text-amber-700 dark:text-amber-400', border: 'border-amber-200 dark:border-amber-800/40', label: 'Medium Risk' }
    return { bg: 'bg-rose-50 dark:bg-rose-950/30', text: 'text-rose-700 dark:text-rose-400', border: 'border-rose-200 dark:border-rose-800/40', label: 'High Risk' }
  }

  // Portfolio-level KPI aggregates
  const lowRiskCount = businesses.filter(b => b.risk_tier === 'Low Risk').length
  const medRiskCount = businesses.filter(b => b.risk_tier === 'Medium Risk').length
  const highRiskCount = businesses.filter(b => b.risk_tier === 'High Risk').length
  const portfolioAvgScore = businesses.length > 0 ? roundToDecimal(businesses.reduce((acc, b) => acc + b.credit_score, 0) / businesses.length, 1) : 0.0

  // Highlighted Wednesday transaction count mock data matching screenshot bar chart
  const weeklyTxnData = [
    { day: 'Mo', count: 420 },
    { day: 'Tu', count: 680 },
    { day: 'Wed', count: 1308, highlighted: true },
    { day: 'Thu', count: 520 },
    { day: 'Fr', count: 610 },
    { day: 'Sat', count: 350 },
    { day: 'Sun', count: 210 }
  ];

  // Group portfolio stats for categories
  const getCategoryRiskStats = () => {
    const categories = ['Gym', 'Salon', 'Cafe', 'Retail'];
    return categories.map(cat => {
      const peers = businesses.filter(b => b.category === cat);
      const avgScore = peers.length > 0 ? peers.reduce((acc, p) => acc + p.credit_score, 0) / peers.length : 50;
      // Inflow mapping to draw the dual bar chart like in the screenshot
      const avgVolume = cat === 'Gym' ? 18000 : cat === 'Salon' ? 24000 : cat === 'Cafe' ? 46820 : 32000;
      const avgOutflow = cat === 'Gym' ? 12000 : cat === 'Salon' ? 16000 : cat === 'Cafe' ? 32000 : 21000;
      return {
        category: cat,
        "Inflow": avgVolume,
        "Outflow": avgOutflow,
        "Avg Score": Math.round(avgScore)
      };
    });
  };

  const categoryStats = getCategoryRiskStats();

  // Model comparison metadata for evaluation tab
  const modelMetricsData = [
    { name: 'Stacking Champion', AUC: 0.796, F1: 0.784, Brier: 0.187 },
    { name: 'Random Forest', AUC: 0.795, F1: 0.787, Brier: 0.191 },
    { name: 'XGBoost Tuned', AUC: 0.791, F1: 0.759, Brier: 0.194 },
    { name: 'LightGBM Tuned', AUC: 0.789, F1: 0.771, Brier: 0.195 },
    { name: 'Logistic Reg', AUC: 0.788, F1: 0.783, Brier: 0.193 }
  ];

  // =========================================================================
  // RENDER LOGIN SCREEN (IF NOT AUTHENTICATED)
  // =========================================================================
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-[#F4F7F5] dark:bg-[#071510] relative overflow-hidden transition-colors duration-200">
        
        {/* Dark Mode toggle on Login Screen */}
        <div className="absolute top-6 right-6">
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="p-2.5 rounded-xl border border-gray-200 dark:border-forest-800/40 bg-white dark:bg-[#0f2a21] text-gray-500 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-[#173F32] transition-all shadow-sm"
            aria-label="Toggle Dark Mode"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>

        {/* Decorative Background Curves */}
        <div className="absolute -left-20 -bottom-20 w-80 h-80 bg-emerald-500/10 dark:bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-emerald-500/10 dark:bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>

        {/* Login Card */}
        <div className="w-full max-w-md p-8 bg-white dark:bg-[#0f2a21]/90 border border-gray-200/50 dark:border-forest-800/30 shadow-[0_10px_35px_-5px_rgba(0,0,0,0.06)] rounded-[28px] z-10 flex flex-col items-center">
          
          {/* Brand Header */}
          <div className="bg-[#0F2A21] dark:bg-emerald-500 text-white p-3 rounded-2xl flex items-center justify-center shadow-md mb-4">
            <Database size={24} className="text-emerald-400 dark:text-white" />
          </div>
          <h2 className="font-outfit text-2xl font-bold text-[#0F2A21] dark:text-white tracking-tight">AlternaTrust Portal</h2>
          <p className="text-xs text-gray-400 mt-1 mb-8">AI-Powered Underwriting Risk Engine</p>
          
          {/* Login Form */}
          <form onSubmit={handleLoginSubmit} className="w-full space-y-5">
            
            {/* Username field */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3.5 text-gray-400" size={14} />
                <input 
                  type="email" 
                  required
                  placeholder="analyst@alternatrust.com"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[#F4F7F5] dark:bg-forest-950 border border-transparent focus:border-emerald-500 dark:focus:border-emerald-400 focus:bg-white dark:focus:bg-[#081712] pl-10 pr-4 py-3 text-xs rounded-xl outline-none transition-all placeholder:text-gray-400 text-[#0F2A21] dark:text-white"
                />
              </div>
            </div>

            {/* Password field */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 text-gray-400" size={14} />
                <input 
                  type="password" 
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#F4F7F5] dark:bg-forest-950 border border-transparent focus:border-emerald-500 dark:focus:border-emerald-400 focus:bg-white dark:focus:bg-[#081712] pl-10 pr-4 py-3 text-xs rounded-xl outline-none transition-all placeholder:text-gray-400 text-[#0F2A21] dark:text-white"
                />
              </div>
            </div>

            {/* Credentials help hint */}
            <div className="text-[10px] text-gray-400 leading-normal flex items-start gap-1.5 bg-gray-50 dark:bg-[#081712] p-2.5 rounded-xl border border-gray-100 dark:border-forest-900/20">
              <Info size={14} className="shrink-0 text-emerald-500 mt-0.5" />
              <span>Hint: Use <strong>analyst@alternatrust.com</strong> & password <strong>admin123</strong> to sign in.</span>
            </div>

            {/* Error state */}
            {loginError && (
              <div className="text-[10px] font-bold text-rose-600 bg-rose-50 dark:bg-rose-950/20 py-2 px-3 rounded-lg flex items-center gap-1.5 border border-rose-100 dark:border-rose-900/30 animate-shake">
                <AlertTriangle size={12} />
                <span>{loginError}</span>
              </div>
            )}

            {/* Submit button */}
            <button 
              type="submit"
              className="w-full bg-[#0F2A21] dark:bg-emerald-500 hover:bg-[#1E4D3E] dark:hover:bg-emerald-600 text-white font-bold text-xs py-3.5 rounded-2xl shadow-sm transition-all mt-2 cursor-pointer"
            >
              Sign In to Portal
            </button>

          </form>

        </div>

      </div>
    )
  }

  // =========================================================================
  // RENDER APP CONTENT (IF LOGGED IN)
  // =========================================================================
  return (
    <div className="flex h-screen bg-[#F4F7F5] dark:bg-[#071510] font-sans antialiased text-[#0E3527] dark:text-slate-100 overflow-hidden transition-colors duration-200">
      
      {/* ==================== LEFT SIDEBAR ==================== */}
      <aside className="w-64 bg-white dark:bg-[#081712] text-gray-700 dark:text-white flex flex-col justify-between shrink-0 h-full border-r border-gray-200/50 dark:border-forest-900/30 transition-all duration-200">
        <div className="flex flex-col flex-1 overflow-y-auto">
          
          {/* Logo / Brand container */}
          <div className="p-4 mt-2">
            <div className="bg-[#F4F7F5] dark:bg-[#0f2a21]/60 border border-gray-200 dark:border-forest-800/40 p-3 rounded-2xl flex items-center justify-between cursor-pointer hover:bg-gray-100 dark:hover:bg-[#1E4D3E] transition-all">
              <div className="flex items-center gap-2.5">
                <div className="bg-[#0F2A21] dark:bg-emerald-500 text-white p-2 rounded-xl flex items-center justify-center shadow-sm">
                  <Database size={16} />
                </div>
                <div className="flex flex-col">
                  <span className="font-outfit text-sm font-bold tracking-tight text-[#0F2A21] dark:text-white">AlternaTrust</span>
                  <span className="text-[10px] text-[#0F2A21]/70 dark:text-emerald-400 font-semibold tracking-wider uppercase">Credit Engine</span>
                </div>
              </div>
              <ChevronDown size={14} className="text-gray-550 dark:text-forest-300" />
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-4 py-6 space-y-1">
            <button 
              onClick={() => { setView('portfolio'); setSelectedBusiness(null); }}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl font-medium text-xs tracking-wider uppercase transition-all ${view === 'portfolio' ? 'bg-[#F4F7F5] dark:bg-[#173F32] text-[#0F2A21] dark:text-emerald-400 font-bold shadow-sm border-l-2 border-[#0F2A21] dark:border-emerald-400' : 'text-gray-500 dark:text-forest-300 hover:bg-[#F4F7F5]/80 dark:hover:bg-[#173F32]/50 hover:text-[#0F2A21] dark:hover:text-white'}`}
            >
              <Layers size={16} />
              Dashboard
            </button>

            <button 
              onClick={() => {
                if (selectedBusiness) {
                  setView('detail');
                } else {
                  alert("Please select a business from the portfolio list first.");
                }
              }}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl font-medium text-xs tracking-wider uppercase transition-all ${view === 'detail' ? 'bg-[#F4F7F5] dark:bg-[#173F32] text-[#0F2A21] dark:text-emerald-400 font-bold shadow-sm border-l-2 border-[#0F2A21] dark:border-emerald-400' : 'text-gray-500 dark:text-forest-300 hover:bg-[#F4F7F5]/80 dark:hover:bg-[#173F32]/50 hover:text-[#0F2A21] dark:hover:text-white'}`}
            >
              <Activity size={16} />
              Underwriting Analysis
            </button>

            <button 
              onClick={() => setView('batch')}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl font-medium text-xs tracking-wider uppercase transition-all ${view === 'batch' ? 'bg-[#F4F7F5] dark:bg-[#173F32] text-[#0F2A21] dark:text-emerald-400 font-bold shadow-sm border-l-2 border-[#0F2A21] dark:border-emerald-400' : 'text-gray-500 dark:text-forest-300 hover:bg-[#F4F7F5]/80 dark:hover:bg-[#173F32]/50 hover:text-[#0F2A21] dark:hover:text-white'}`}
            >
              <Upload size={16} />
              Batch Underwriting
            </button>

            <button 
              onClick={() => setView('metrics')}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl font-medium text-xs tracking-wider uppercase transition-all ${view === 'metrics' ? 'bg-[#F4F7F5] dark:bg-[#173F32] text-[#0F2A21] dark:text-emerald-400 font-bold shadow-sm border-l-2 border-[#0F2A21] dark:border-emerald-400' : 'text-gray-500 dark:text-forest-300 hover:bg-[#F4F7F5]/80 dark:hover:bg-[#173F32]/50 hover:text-[#0F2A21] dark:hover:text-white'}`}
            >
              <ShieldCheck size={16} />
              Model Performance
            </button>
          </nav>

        </div>

        {/* Footer actions / Sign Out */}
        <div className="p-4 border-t border-gray-200 dark:border-[#153B2F]/60 space-y-3.5">
          <button 
            onClick={() => {
              setIsLoggedIn(false);
              setUsername('');
              setPassword('');
            }}
            className="w-full flex items-center justify-center gap-2 font-bold text-[10px] py-2.5 px-3 rounded-xl border border-rose-200 dark:border-rose-900/30 text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/10 hover:bg-rose-100 dark:hover:bg-rose-950/30 transition-all uppercase tracking-wider cursor-pointer"
          >
            <LogOut size={12} />
            Sign Out
          </button>
          
          <div className="text-[10px] text-center text-gray-400 dark:text-forest-400 font-medium pb-1 font-mono">
            AlternaTrust Engine v1.0
          </div>
        </div>
      </aside>

      {/* ==================== MAIN CONTENT AREA ==================== */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        
        {/* TOP NAVBAR */}
        <header className="h-16 px-8 flex items-center justify-between border-b border-gray-200/50 dark:border-forest-900/20 bg-white/60 dark:bg-[#0f2a21]/20 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="font-outfit text-xl font-bold tracking-tight text-[#0F2A21] dark:text-white">
              {view === 'portfolio' && "Merchant Risk Dashboard"}
              {view === 'detail' && "Credit Score Underwriting Report"}
              {view === 'batch' && "Batch Credit Underwriting"}
              {view === 'metrics' && "Champion Model Evaluation"}
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Theme Segmented Switch Switch to enable white and dark mode */}
            <div className="flex bg-[#F4F7F5] dark:bg-forest-950 p-1 rounded-xl border border-gray-200/50 dark:border-forest-800/40">
              <button 
                onClick={() => setDarkMode(false)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all cursor-pointer font-outfit ${!darkMode ? 'bg-white text-[#0f2a21] shadow-sm' : 'text-gray-400'}`}
              >
                <Sun size={12} />
                Light
              </button>
              <button 
                onClick={() => setDarkMode(true)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all cursor-pointer font-outfit ${darkMode ? 'bg-[#173F32] text-emerald-400 shadow-sm' : 'text-gray-400'}`}
              >
                <Moon size={12} />
                Dark
              </button>
            </div>

            <button 
              onClick={() => setView('batch')}
              className="bg-[#0F2A21] dark:bg-emerald-500 hover:bg-[#183E31] dark:hover:bg-emerald-600 text-white font-semibold text-xs py-2.5 px-4 rounded-xl flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
            >
              <Plus size={14} />
              Create Underwrite
            </button>
          </div>
        </header>

        {/* WORKSPACE CONTENT SCROLLABLE ZONE */}
        <main className="flex-1 overflow-y-auto p-8 space-y-8">
          
          {/* ========================================================================= */}
          {/* 1. PORTFOLIO DASHBOARD VIEW */}
          {/* ========================================================================= */}
          {view === 'portfolio' && (
            <div className="space-y-8 animate-fadeIn">
              
              {/* Row 1 Grid (Tall card, metrics stack, Money insights chart) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                {/* Column A: Connect alternative database card */}
                <div className="lg:col-span-3 bg-gradient-to-br from-[#062B1E] to-[#125843] text-white p-7 rounded-[28px] relative overflow-hidden flex flex-col justify-between min-h-[340px] shadow-[0_4px_25px_rgba(6,43,30,0.15)] border border-[#164839]">
                  {/* Abstract background SVG curves inspired by mockup visual overlay */}
                  <div className="absolute -right-4 -top-4 w-32 h-32 bg-emerald-400/20 rounded-full blur-2xl pointer-events-none"></div>
                  <svg className="absolute right-0 bottom-0 opacity-25 pointer-events-none" width="160" height="160" viewBox="0 0 100 100">
                    <path d="M0,75 Q25,50 50,75 T100,75 L100,100 L0,100 Z" fill="#34D399" />
                    <path d="M0,85 Q20,65 50,85 T100,85 L100,100 L0,100 Z" fill="#A7F3D0" />
                  </svg>
                  
                  <div>
                    <h2 className="font-outfit text-xl font-bold leading-snug tracking-tight max-w-[200px] mb-2.5">
                      Connect your bank account or alternative data
                    </h2>
                    <p className="text-[11px] text-emerald-200/90 leading-relaxed max-w-[180px]">
                      Automate your underwriting metrics by importing live UPI transactions, footfalls and reviews.
                    </p>
                  </div>
                  
                  <button 
                    onClick={() => setView('batch')}
                    className="bg-[#D9F99D] hover:bg-[#C5F246] text-[#062B1E] font-bold text-xs py-3 px-5 rounded-2xl w-fit transition-all shadow-md z-10 cursor-pointer"
                  >
                    Connect account
                  </button>
                </div>

                {/* Column B: Stack of KPI metrics (Overall Revenue, Invoiced, Received, Clients styling) */}
                <div className="lg:col-span-3 flex flex-col gap-[14px]">
                  
                  {/* KPI 1: Average Score */}
                  <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                    <div>
                      <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">Avg Credit Score</span>
                      <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                        {portfolioLoading ? "..." : `${portfolioAvgScore}/100`}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                        <TrendingUp size={10} />
                        +3.6%
                      </span>
                      <div className="bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-400 p-3 rounded-2xl shrink-0">
                        <Award size={20} />
                      </div>
                    </div>
                  </div>

                  {/* KPI 2: Low Risk */}
                  <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                    <div>
                      <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">Low Risk (Active)</span>
                      <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                        {portfolioLoading ? "..." : lowRiskCount}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                        <TrendingUp size={10} />
                        +5.04%
                      </span>
                      <div className="bg-teal-100 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 p-3 rounded-2xl shrink-0">
                        <ShieldCheck size={20} />
                      </div>
                    </div>
                  </div>

                  {/* KPI 3: Medium Risk */}
                  <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                    <div>
                      <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">Medium Risk</span>
                      <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                        {portfolioLoading ? "..." : medRiskCount}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                        <TrendingDown size={10} />
                        -2.05%
                      </span>
                      <div className="bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 p-3 rounded-2xl shrink-0">
                        <Activity size={20} />
                      </div>
                    </div>
                  </div>

                  {/* KPI 4: High Risk */}
                  <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                    <div>
                      <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">High Risk (Watch)</span>
                      <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                        {portfolioLoading ? "..." : highRiskCount}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                        <TrendingUp size={10} />
                        +1.3%
                      </span>
                      <div className="bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 p-3 rounded-2xl shrink-0">
                        <AlertTriangle size={20} />
                      </div>
                    </div>
                  </div>

                </div>

                {/* Column C: Money insights chart (Large bar chart) */}
                <div className="lg:col-span-6 glass-panel p-6 flex flex-col justify-between min-h-[340px]">
                  <div className="flex items-center justify-between border-b border-gray-100 dark:border-forest-900/20 pb-4 mb-4">
                    <div>
                      <h2 className="font-outfit text-base font-bold text-[#0F2A21] dark:text-white">Money insights</h2>
                      <span className="text-xs text-gray-400 dark:text-gray-400 font-medium">Cash coming in and going out of your business (Industry Cohort Averages)</span>
                    </div>
                    <button 
                      onClick={() => setView('metrics')}
                      className="text-xs font-semibold px-4.5 py-2 border border-gray-200 dark:border-forest-800/40 text-[#0F2A21] dark:text-slate-300 rounded-xl hover:bg-gray-50 dark:hover:bg-[#173F32] transition-all cursor-pointer"
                    >
                      View report
                    </button>
                  </div>
                  
                  <div className="h-44 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={categoryStats} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? "#153b2f" : "#e6f2ed"} />
                        <XAxis dataKey="category" stroke="#94a3b8" tickLine={false} axisLine={false} tick={{ fontSize: 11, fontWeight: 500 }} />
                        <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val/1000}k`} tick={{ fontSize: 11 }} />
                        <Tooltip 
                          formatter={(value) => [`₹${value.toLocaleString()}`, "Weekly Volume"]}
                          contentStyle={{ backgroundColor: darkMode ? '#0e221b' : '#ffffff', borderColor: darkMode ? '#153b2f' : '#e6f2ed', borderRadius: '16px', fontSize: 11, color: darkMode ? '#ffffff' : '#000000' }}
                        />
                        <Legend verticalAlign="bottom" height={24} iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 10, fontWeight: 600 }} />
                        {/* Bars matching the mockup color scheme: dark forest green and teal */}
                        <Bar name="Inflow" dataKey="Inflow" fill="#10B981" radius={[6, 6, 0, 0]} maxBarSize={30} />
                        <Bar name="Outflow" dataKey="Outflow" fill={darkMode ? "#a3d1bf" : "#0F2A21"} radius={[6, 6, 0, 0]} maxBarSize={30} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

              </div>

              {/* Row 2 Grid (Total orders, Recent Invoices) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                {/* Total orders style card with Wednesday highlighted bar chart */}
                <div className="lg:col-span-5 glass-panel p-6 flex flex-col justify-between min-h-[360px]">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="font-outfit text-base font-bold text-[#0F2A21] dark:text-white">Total orders</h2>
                      <div className="flex items-baseline gap-2 mt-2">
                        <span className="text-3xl font-bold font-outfit text-[#0F2A21] dark:text-white">3,021</span>
                        <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950/40 py-0.5 px-2 rounded-full flex items-center gap-0.5">
                          +164 increase <TrendingUp size={8} />
                        </span>
                      </div>
                    </div>
                    
                    <select className="bg-gray-50 dark:bg-[#081712] border border-gray-200 dark:border-forest-800/40 text-xs font-semibold px-3 py-1.5 rounded-xl outline-none text-[#0f2a21] dark:text-slate-300">
                      <option>Weekly</option>
                      <option>Monthly</option>
                    </select>
                  </div>

                  {/* Highlights Wednesday like in mock */}
                  <div className="h-44 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={weeklyTxnData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                        <XAxis dataKey="day" stroke="#94a3b8" tickLine={false} axisLine={false} tick={{ fontSize: 11, fontWeight: 500 }} />
                        <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                        <Tooltip 
                          formatter={(value) => [value, "Transactions"]}
                          contentStyle={{ backgroundColor: darkMode ? '#0e221b' : '#ffffff', borderColor: darkMode ? '#153b2f' : '#e2e8f0', borderRadius: '12px' }}
                        />
                        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                          {weeklyTxnData.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={entry.highlighted ? (darkMode ? "#10B981" : "#0F2A21") : (darkMode ? "#153b2f" : "#E2E8F0")} 
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  {/* Highlight label */}
                  <div className="text-[10px] text-center text-gray-400 font-semibold uppercase mt-3 tracking-wider">
                    Peak transaction volume on Wednesday (1,308 txns)
                  </div>
                </div>

                {/* Recent invoices style scored merchants table */}
                <div className="lg:col-span-7 glass-panel p-6 flex flex-col justify-between min-h-[360px] overflow-hidden">
                  <div>
                    
                    {/* Header with Search and inline Filters */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-100 dark:border-forest-900/20 pb-4 mb-4 gap-3">
                      <div>
                        <h2 className="font-outfit text-base font-bold text-[#0F2A21] dark:text-white">Recent invoices</h2>
                        <span className="text-[11px] text-gray-400 dark:text-gray-400 font-medium">Scored credit risk portfolio list of micro-merchants</span>
                      </div>
                      
                      {/* Search box inline */}
                      <div className="relative">
                        <Search className="absolute left-3 top-2.5 text-gray-400" size={14} />
                        <input 
                          type="text"
                          placeholder="Search..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="bg-[#F4F7F5] dark:bg-forest-950 border-0 focus:ring-1 focus:ring-[#0F2A21] dark:focus:ring-emerald-500 pl-8 pr-3 py-1.5 text-xs rounded-xl outline-none transition-all placeholder:text-gray-400 w-36 sm:w-44 text-[#0f2a21] dark:text-slate-100"
                        />
                      </div>
                    </div>

                    {/* Filter Strip */}
                    <div className="flex flex-wrap items-center gap-2 mb-4 bg-gray-50/50 dark:bg-[#081712] p-2 rounded-xl border border-gray-100 dark:border-forest-800/20">
                      <select 
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                        className="bg-white dark:bg-[#0e221b] border border-gray-150 dark:border-forest-800/40 text-[10px] font-semibold px-2 py-1 rounded-lg text-gray-600 dark:text-slate-300 outline-none"
                      >
                        <option value="All">All Sectors</option>
                        <option value="Gym">Gym</option>
                        <option value="Salon">Salon</option>
                        <option value="Cafe">Cafe</option>
                        <option value="Retail">Retail</option>
                      </select>
                      
                      <select 
                        value={riskFilter}
                        onChange={(e) => setRiskFilter(e.target.value)}
                        className="bg-white dark:bg-[#0e221b] border border-gray-150 dark:border-forest-800/40 text-[10px] font-semibold px-2 py-1 rounded-lg text-gray-600 dark:text-slate-300 outline-none"
                      >
                        <option value="All">All Risk</option>
                        <option value="Low Risk">Low</option>
                        <option value="Medium Risk">Medium</option>
                        <option value="High Risk">High</option>
                      </select>
                    </div>

                    {/* Table View */}
                    <div className="overflow-x-auto max-h-48 overflow-y-auto">
                      <table className="w-full text-left border-collapse text-[11px]">
                        <thead>
                          <tr className="border-b border-gray-100 dark:border-forest-900/20 text-[10px] font-bold text-gray-400 uppercase">
                            <th className="py-2.5">Status</th>
                            <th className="py-2.5">Merchant ID</th>
                            <th className="py-2.5">Business & Owner</th>
                            <th className="py-2.5">Risk Score</th>
                            <th className="py-2.5 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {portfolioLoading ? (
                            Array.from({ length: 4 }).map((_, idx) => (
                              <tr key={idx} className="border-b border-gray-50 dark:border-forest-900/10 animate-pulse">
                                <td className="py-3"><div className="h-5 bg-gray-200 dark:bg-forest-800 w-16 rounded"></div></td>
                                <td className="py-3"><div className="h-4 bg-gray-200 dark:bg-forest-800 w-12 rounded"></div></td>
                                <td className="py-3"><div className="h-4 bg-gray-200 dark:bg-forest-800 w-28 rounded"></div></td>
                                <td className="py-3"><div className="h-4 bg-gray-200 dark:bg-forest-800 w-8 rounded"></div></td>
                                <td className="py-3 text-right"><div className="h-6 bg-gray-200 dark:bg-forest-800 w-12 rounded ml-auto"></div></td>
                              </tr>
                            ))
                          ) : filteredBiz.length === 0 ? (
                            <tr>
                              <td colSpan="5" className="py-8 text-center text-gray-400">
                                No records found matching the search filters.
                              </td>
                            </tr>
                          ) : (
                            filteredBiz.map((b) => {
                              const colors = getRiskColor(b.risk_tier)
                              return (
                                <tr 
                                  key={b.business_id}
                                  className="border-b border-gray-50/50 dark:border-forest-900/10 hover:bg-[#F4F7F5]/50 dark:hover:bg-[#0e221b]/40 transition-colors"
                                >
                                  <td className="py-3">
                                    <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold tracking-wide uppercase ${colors.bg} ${colors.text}`}>
                                      {colors.label}
                                    </span>
                                  </td>
                                  <td className="py-3 font-mono font-bold text-gray-400">{b.business_id}</td>
                                  <td className="py-3">
                                    <span 
                                      onClick={() => handleViewDetails(b.business_id)}
                                      className="font-bold text-[#0F2A21] dark:text-white hover:underline cursor-pointer block"
                                    >
                                      {b.business_name}
                                    </span>
                                    <span className="text-[10px] text-gray-450 dark:text-gray-400">{b.owner_name} • {b.category}</span>
                                  </td>
                                  <td className="py-3 font-bold text-[#0F2A21] dark:text-slate-100">{b.credit_score}</td>
                                  <td className="py-3 text-right">
                                    <button 
                                      onClick={() => handleViewDetails(b.business_id)}
                                      className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 px-3 py-1 rounded-xl border border-emerald-100 dark:border-emerald-900/30 hover:bg-emerald-100 hover:text-emerald-800 transition-all cursor-pointer"
                                    >
                                      View
                                    </button>
                                  </td>
                                </tr>
                              )
                            })
                          )}
                        </tbody>
                      </table>
                    </div>

                  </div>
                  
                  {/* Footer */}
                  <div className="pt-3 border-t border-gray-100 dark:border-forest-900/20 flex items-center justify-between text-[10px] text-gray-400">
                    <span>Showing {filteredBiz.length} of {businesses.length} items</span>
                    <span className="font-semibold text-[#0F2A21] dark:text-slate-300">AlternaTrust Classifier</span>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* 2. DETAILED MERCHANT ANALYSIS VIEW */}
          {/* ========================================================================= */}
          {view === 'detail' && (
            <div className="space-y-8 animate-fadeIn">
              
              {/* Back button */}
              <button 
                onClick={() => { setView('portfolio'); setSelectedBusiness(null); }}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-[#0F2A21] dark:text-slate-300 transition-all font-semibold uppercase tracking-wider bg-white dark:bg-[#0e221b] py-2 px-4 rounded-xl shadow-sm border border-gray-100 dark:border-forest-800/20 cursor-pointer"
              >
                <ArrowLeft size={14} />
                Back to dashboard
              </button>

              {loading || !selectedBusiness ? (
                <div className="animate-pulse space-y-8">
                  <div className="h-8 bg-gray-200 dark:bg-forest-800 w-1/3 rounded-lg"></div>
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    <div className="lg:col-span-3 h-80 bg-gray-200 dark:bg-forest-800 rounded-3xl"></div>
                    <div className="lg:col-span-3 h-80 bg-gray-200 dark:bg-forest-800 rounded-3xl"></div>
                    <div className="lg:col-span-6 h-80 bg-gray-200 dark:bg-forest-800 rounded-3xl"></div>
                  </div>
                </div>
              ) : (
                <div className="space-y-8">
                  
                  {/* Header Detail */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-[#0e221b] p-6 rounded-[24px] border border-gray-100 dark:border-forest-800/20">
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-gray-450 dark:text-gray-450 uppercase tracking-widest font-bold">Business Registry</span>
                        <ChevronRight size={12} className="text-gray-400" />
                        <span className="font-mono text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 px-2 py-0.5 rounded">{selectedBusiness.metadata.business_id}</span>
                      </div>
                      <h2 className="font-outfit text-2xl font-bold mt-1 text-[#0F2A21] dark:text-white">
                        {selectedBusiness.metadata.business_name}
                      </h2>
                      <p className="text-xs text-gray-400 mt-1">
                        Owner: <strong className="text-gray-600 dark:text-slate-300">{selectedBusiness.metadata.owner_name}</strong> • City: <strong className="text-gray-600 dark:text-slate-300">{selectedBusiness.metadata.city}</strong> • Experience: <strong className="text-gray-600 dark:text-slate-300">{selectedBusiness.metadata.years_in_operation || 'N/A'} years</strong>
                      </p>
                    </div>

                    <div className={`px-4.5 py-2.5 rounded-2xl text-xs font-bold border flex items-center gap-2 ${getRiskColor(selectedBusiness.metadata.risk_tier).bg} ${getRiskColor(selectedBusiness.metadata.risk_tier).text} ${getRiskColor(selectedBusiness.metadata.risk_tier).border}`}>
                      <ShieldCheck size={16} />
                      {selectedBusiness.metadata.risk_tier.toUpperCase()} CERTIFIED
                    </div>
                  </div>

                  {/* Row 1 Grid (Banner, Metrics, Area Telemetry chart) */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    
                    {/* Tall card Left (Connect account style) */}
                    <div className="lg:col-span-3 bg-gradient-to-br from-[#062B1E] to-[#125843] text-white p-7 rounded-[28px] relative overflow-hidden flex flex-col justify-between min-h-[340px] shadow-[0_4px_25px_rgba(6,43,30,0.15)] border border-[#164839]">
                      <div className="absolute -right-4 -top-4 w-32 h-32 bg-emerald-400/20 rounded-full blur-2xl pointer-events-none"></div>
                      <svg className="absolute right-0 bottom-0 opacity-25 pointer-events-none" width="160" height="160" viewBox="0 0 100 100">
                        <path d="M0,75 Q25,50 50,75 T100,75 L100,100 L0,100 Z" fill="#34D399" />
                      </svg>
                      
                      <div>
                        <h2 className="font-outfit text-xl font-bold leading-snug tracking-tight max-w-[200px] mb-2.5">
                          Underwrite Status Certified
                        </h2>
                        <p className="text-[11px] text-emerald-200/90 leading-relaxed max-w-[180px]">
                          This business satisfies the risk parameters. A credit limit up to ₹5,00,000 can be extended.
                        </p>
                      </div>
                      
                      <button 
                        onClick={() => alert("Credit Offer issued successfully to " + selectedBusiness.metadata.business_name)}
                        className="bg-[#D9F99D] hover:bg-[#C5F246] text-[#062B1E] font-bold text-xs py-3 px-5 rounded-2xl w-fit transition-all shadow-md z-10 cursor-pointer"
                      >
                        Issue credit limit
                      </button>
                    </div>

                    {/* Stack of KPI metrics (Overall Revenue, Invoiced, Received, Clients styling) */}
                    <div className="lg:col-span-3 flex flex-col gap-[14px]">
                      
                      {/* Metric 1: Credit Score progress */}
                      <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                        <div>
                          <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">Credit score</span>
                          <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                            {selectedBusiness.metadata.credit_score}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                            Active
                          </span>
                          <div className="bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-400 p-3 rounded-2xl shrink-0">
                            <Award size={20} />
                          </div>
                        </div>
                      </div>

                      {/* Metric 2: 12-month survival */}
                      <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                        <div>
                          <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">12Mo Survival Prob</span>
                          <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                            {(selectedBusiness.metadata.survival_probability * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                            Highly Probable
                          </span>
                          <div className="bg-teal-100 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 p-3 rounded-2xl shrink-0">
                            <ShieldCheck size={20} />
                          </div>
                        </div>
                      </div>

                      {/* Metric 3: Weekly Transactions volume */}
                      <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                        <div>
                          <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">Weekly Transaction Volume</span>
                          <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                            {selectedBusiness.upi_history.length > 0 ? `₹${Math.round(selectedBusiness.upi_history.reduce((acc, h) => acc + h.transaction_volume, 0) / selectedBusiness.upi_history.length).toLocaleString()}` : "₹0"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                            Stable Inflow
                          </span>
                          <div className="bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 p-3 rounded-2xl shrink-0">
                            <Activity size={20} />
                          </div>
                        </div>
                      </div>

                      {/* Metric 4: Reviews Rating */}
                      <div className="bg-white dark:bg-[#0e221b] p-5 rounded-2xl border border-gray-100 dark:border-forest-800/20 flex items-center justify-between shadow-sm">
                        <div>
                          <span className="text-[10px] font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider block">Average reviews rating</span>
                          <span className="text-2xl font-bold font-outfit text-[#0F2A21] dark:text-white mt-1 block">
                            {selectedBusiness.reviews.length > 0 ? `${(selectedBusiness.reviews.reduce((acc, r) => acc + r.rating, 0) / selectedBusiness.reviews.length).toFixed(1)} ★` : "N/A"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 py-1 px-2 rounded-lg flex items-center gap-0.5">
                            Verified
                          </span>
                          <div className="bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 p-3 rounded-2xl shrink-0">
                            <MessageSquare size={20} />
                          </div>
                        </div>
                      </div>

                    </div>

                    {/* Column C: Area Chart of Telemetry */}
                    <div className="lg:col-span-6 glass-panel p-6 flex flex-col justify-between min-h-[340px]">
                      <div className="flex items-center justify-between border-b border-gray-100 dark:border-forest-900/20 pb-4 mb-4">
                        <div className="flex items-center gap-2">
                          <Activity size={16} className="text-emerald-500" />
                          <h2 className="font-outfit text-base font-bold text-[#0F2A21] dark:text-white">Historical sales volume</h2>
                        </div>
                        
                        <div className="flex bg-[#F4F7F5] dark:bg-forest-950 p-1 rounded-xl">
                          <button 
                            onClick={() => setActiveDetailTab('transactions')}
                            className={`px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all ${activeDetailTab === 'transactions' ? 'bg-white text-[#0f2a21] shadow-sm' : 'text-gray-405'}`}
                          >
                            UPI Volume
                          </button>
                          <button 
                            onClick={() => setActiveDetailTab('social')}
                            className={`px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all ${activeDetailTab === 'social' ? 'bg-white text-[#0f2a21] shadow-sm' : 'text-gray-405'}`}
                          >
                            Instagram followers
                          </button>
                        </div>
                      </div>

                      <div className="h-44 w-full">
                        {activeDetailTab === 'transactions' && (
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={selectedBusiness.upi_history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <defs>
                                <linearGradient id="colorUpi" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                                  <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? "#153b2f" : "#e6f2ed"} />
                              <XAxis dataKey="week_start_date" stroke="#94a3b8" tickLine={false} axisLine={false} tickFormatter={(str) => str.substring(5)} />
                              <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val/1000}k`} />
                              <Tooltip 
                                formatter={(value) => [`₹${value.toLocaleString()}`, "Weekly Volume"]}
                                contentStyle={{ backgroundColor: darkMode ? '#0e221b' : '#ffffff', borderColor: darkMode ? '#153b2f' : '#e6f2ed', borderRadius: '16px' }}
                              />
                              <Area type="monotone" dataKey="transaction_volume" stroke="#10B981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorUpi)" />
                            </AreaChart>
                          </ResponsiveContainer>
                        )}

                        {activeDetailTab === 'social' && (
                          <div className="h-full">
                            {selectedBusiness.social_history.length === 0 ? (
                              <div className="h-full flex flex-col items-center justify-center text-center text-gray-405 py-12">
                                No Social Media Synced.
                              </div>
                            ) : (
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={selectedBusiness.social_history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? "#153b2f" : "#e6f2ed"} />
                                  <XAxis dataKey="week_start_date" stroke="#94a3b8" tickLine={false} axisLine={false} tickFormatter={(str) => str.substring(5)} />
                                  <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} />
                                  <Tooltip 
                                    formatter={(value) => [value.toLocaleString(), "Followers"]}
                                    contentStyle={{ backgroundColor: darkMode ? '#0e221b' : '#ffffff', borderColor: darkMode ? '#153b2f' : '#e6f2ed', borderRadius: '16px' }}
                                  />
                                  <Line type="monotone" dataKey="follower_count" stroke={darkMode ? "#10B981" : "#0F2A21"} strokeWidth={2.5} dot={false} />
                                </LineChart>
                              </ResponsiveContainer>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                  </div>

                  {/* Row 2 Grid (SHAP Attributions progress bar card, review lists & benchmark) */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    
                    {/* Attributions list card (Left, 5/12 span) */}
                    <div className="lg:col-span-5 glass-panel p-6 flex flex-col justify-between min-h-[360px]">
                      <div className="border-b border-gray-100 dark:border-forest-900/20 pb-4 mb-4">
                        <h2 className="font-outfit text-base font-bold text-[#0F2A21] dark:text-white">SHAP Credit Attributions</h2>
                        <span className="text-[10px] text-gray-400 font-medium">Features contributing positive or negative weights on risk score</span>
                      </div>

                      <div className="flex-1 overflow-y-auto max-h-56 pr-2 space-y-4">
                        {selectedBusiness.metadata.top_factors.map((factor, idx) => {
                          const isPos = factor.impact === 'positive'
                          const pct = Math.min(100, Math.max(5, Math.abs(factor.contribution) * 450))
                          return (
                            <div key={idx} className="flex flex-col text-[11px]">
                              <div className="flex items-center justify-between font-medium mb-1">
                                <span className="text-[#0F2A21] dark:text-slate-300 truncate max-w-[70%]" title={factor.description}>
                                  {factor.description}
                                </span>
                                <span className={`font-mono font-bold ${isPos ? 'text-emerald-600' : 'text-rose-600'}`}>
                                  {isPos ? '+' : ''}{factor.contribution.toFixed(4)}
                                </span>
                              </div>
                              <div className="w-full h-2 bg-[#F4F7F5] dark:bg-forest-950 rounded-full overflow-hidden flex">
                                {isPos ? (
                                  <div className="h-full bg-emerald-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }}></div>
                                ) : (
                                  <div className="ml-auto h-full bg-rose-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }}></div>
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>

                      {/* Info footnote */}
                      <span className="text-[9px] text-gray-400 mt-2 block font-medium leading-relaxed">
                        *SHAP attributions indicate directional influence on the stacking meta-classifier.
                      </span>
                    </div>

                    {/* Review lists/sentiment/benchmark table (Right, 7/12 span) */}
                    <div className="lg:col-span-7 glass-panel p-6 flex flex-col justify-between min-h-[360px]">
                      <div>
                        
                        <div className="flex items-center justify-between border-b border-gray-100 dark:border-forest-900/20 pb-4 mb-4">
                          <h2 className="font-outfit text-base font-bold text-[#0F2A21] dark:text-white">Customer feedback & feedback analysis</h2>
                          
                          <div className="flex bg-[#F4F7F5] dark:bg-forest-950 p-1 rounded-xl">
                            <button 
                              onClick={() => setActiveDetailTab('reviews')}
                              className={`px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all ${activeDetailTab === 'reviews' ? 'bg-white text-[#0f2a21] shadow-sm' : 'text-gray-405'}`}
                            >
                              Recent Reviews
                            </button>
                            <button 
                              onClick={() => setActiveDetailTab('comparison')}
                              className={`px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all ${activeDetailTab === 'comparison' ? 'bg-white text-[#0f2a21] shadow-sm' : 'text-gray-405'}`}
                            >
                              Cohort Benchmark
                            </button>
                          </div>
                        </div>

                        {/* Sub tab: Reviews list */}
                        {activeDetailTab === 'reviews' && (
                          <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                            {selectedBusiness.reviews.length === 0 ? (
                              <div className="text-center py-8 text-gray-450 text-xs">
                                No reviews recorded.
                              </div>
                            ) : (
                              selectedBusiness.reviews.map((rev, idx) => (
                                <div key={idx} className="p-3 bg-gray-50 dark:bg-forest-950/40 rounded-xl border border-gray-100 dark:border-forest-800/10 flex flex-col gap-1 text-[11px]">
                                  <div className="flex items-center justify-between">
                                    <div className="flex gap-0.5">
                                      {Array.from({ length: 5 }).map((_, s) => (
                                        <span key={s} className={`text-xs ${s < rev.rating ? 'text-amber-400' : 'text-gray-200'}`}>★</span>
                                      ))}
                                    </div>
                                    <span className="text-[10px] text-gray-400 font-semibold">{rev.date}</span>
                                  </div>
                                  <p className="italic text-gray-605 dark:text-slate-300">"{rev.review_text}"</p>
                                </div>
                              ))
                            )}
                          </div>
                        )}

                        {/* Sub tab: Comparison metrics table */}
                        {activeDetailTab === 'comparison' && (
                          <div className="overflow-x-auto max-h-48 overflow-y-auto">
                            <table className="w-full text-left border-collapse text-[11px]">
                              <thead>
                                <tr className="border-b border-gray-100 dark:border-forest-900/20 text-gray-400 font-bold uppercase">
                                  <th className="py-2">Metric</th>
                                  <th className="py-2">This Business</th>
                                  <th className="py-2">Cohort Avg</th>
                                  <th className="py-2 text-right">Difference</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr className="border-b border-gray-50 dark:border-forest-900/10">
                                  <td className="py-3 font-semibold">Credit Risk Score</td>
                                  <td className="py-3 font-bold">{selectedBusiness.metadata.credit_score}</td>
                                  <td className="py-3 text-gray-500">{getPeerAverages()?.score}</td>
                                  <td className="py-3 text-right font-bold">
                                    {selectedBusiness.metadata.credit_score >= (getPeerAverages()?.score || 50) ? (
                                      <span className="text-emerald-600 font-bold">+{roundToDecimal(selectedBusiness.metadata.credit_score - (getPeerAverages()?.score || 50), 1)}</span>
                                    ) : (
                                      <span className="text-rose-600 font-bold">-{roundToDecimal((getPeerAverages()?.score || 50) - selectedBusiness.metadata.credit_score, 1)}</span>
                                    )}
                                  </td>
                                </tr>

                                <tr className="border-b border-gray-50 dark:border-forest-900/10">
                                  <td className="py-3 font-semibold">Years Operating</td>
                                  <td className="py-3 font-bold">{selectedBusiness.metadata.years_in_operation || "N/A"}</td>
                                  <td className="py-3 text-gray-500">{getPeerAverages()?.years}</td>
                                  <td className="py-3 text-right font-bold">
                                    {selectedBusiness.metadata.years_in_operation >= (getPeerAverages()?.years || 2) ? (
                                      <span className="text-emerald-600 font-bold">+{roundToDecimal(selectedBusiness.metadata.years_in_operation - (getPeerAverages()?.years || 2), 1)} yrs</span>
                                    ) : (
                                      <span className="text-rose-600 font-bold">-{roundToDecimal((getPeerAverages()?.years || 2) - selectedBusiness.metadata.years_in_operation, 1)} yrs</span>
                                    )}
                                  </td>
                                </tr>

                                <tr className="border-b border-gray-50 dark:border-forest-900/10">
                                  <td className="py-3 font-semibold">Weekly Transactions</td>
                                  <td className="py-3 font-bold">{selectedBusiness.upi_history.length > 0 ? Math.round(selectedBusiness.upi_history.reduce((acc, h) => acc + h.transaction_count, 0) / selectedBusiness.upi_history.length) : 0}</td>
                                  <td className="py-3 text-gray-500">{selectedBusiness.metadata.category === 'Gym' ? '30' : selectedBusiness.metadata.category === 'Salon' ? '50' : selectedBusiness.metadata.category === 'Cafe' ? '210' : '135'}</td>
                                  <td className="py-3 text-right text-gray-400 font-semibold">Baseline</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        )}

                      </div>

                      {/* Actionable recommendations booster */}
                      <div className="mt-4 p-3 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30">
                        <span className="text-[10px] font-bold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider block">Booster action item</span>
                        {selectedBusiness.metadata.top_factors && (
                          <p className="text-[10px] text-emerald-700 dark:text-emerald-300 leading-normal mt-1">
                            Recommendation: <strong>{getActionableRecommendations(selectedBusiness.metadata.top_factors)[0]?.title}</strong> - {getActionableRecommendations(selectedBusiness.metadata.top_factors)[0]?.text}
                          </p>
                        )}
                      </div>
                    </div>

                  </div>

                </div>
              )}

            </div>
          )}

          {/* ========================================================================= */}
          {/* 3. BATCH CSV UPLOADER VIEW */}
          {/* ========================================================================= */}
          {view === 'batch' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fadeIn">
              
              {/* Left pane: File drag and drop */}
              <div className="lg:col-span-5 flex flex-col gap-6">
                <div className="glass-panel p-6">
                  <h2 className="font-outfit font-bold text-base text-[#0F2A21] mb-2 dark:text-white">Batch underwriter uploader</h2>
                  <p className="text-xs text-gray-400 mb-5 leading-relaxed">
                    Upload a list of businesses to queue for automated credit scoring.
                  </p>
                  
                  {/* File upload box */}
                  <div 
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleFileDrop}
                    className="border-2 border-dashed border-[#C5E6DB] dark:border-forest-800/40 rounded-3xl p-8 flex flex-col items-center justify-center text-center hover:border-emerald-500 transition-all cursor-pointer bg-[#F4F7F5]/40 dark:bg-forest-950/20"
                  >
                    <Upload size={32} className="text-gray-400 mb-3" />
                    <span className="text-xs font-bold text-gray-700 dark:text-slate-300">Choose a CSV file or drag it here</span>
                    <span className="text-[9px] text-gray-400 mt-1 block">Maximum size 5MB. Must contain a 'business_id' column.</span>
                    
                    <input 
                      type="file" 
                      id="csv-file-input" 
                      accept=".csv"
                      onChange={handleFileDrop}
                      className="hidden"
                    />
                    
                    <button 
                      onClick={() => document.getElementById('csv-file-input').click()}
                      className="mt-4 text-[10px] font-bold px-4 py-2 border border-gray-200 dark:border-forest-800/40 hover:bg-gray-100 dark:hover:bg-[#173F32] text-emerald-800 dark:text-emerald-400 bg-white dark:bg-[#0e221b] rounded-xl shadow-sm cursor-pointer"
                    >
                      Select file
                    </button>
                  </div>

                  {batchFile && (
                    <div className="mt-4 p-3 bg-emerald-50 dark:bg-[#0e221b] border border-emerald-100 dark:border-forest-800/40 rounded-2xl flex items-center justify-between text-xs">
                      <span className="font-bold text-emerald-800 dark:text-emerald-400 truncate">{batchFile.name}</span>
                      <span className="text-[10px] text-emerald-600 font-semibold">{(batchFile.size / 1024).toFixed(1)} KB</span>
                    </div>
                  )}

                  <button
                    disabled={!batchFile || batchUploading}
                    onClick={handleUploadBatch}
                    className={`w-full mt-6 font-bold text-xs py-3.5 rounded-2xl flex items-center justify-center gap-2 shadow-md transition-all cursor-pointer ${!batchFile || batchUploading ? 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200' : 'bg-[#0F2A21] dark:bg-emerald-500 hover:bg-[#1C4E3D] text-white'}`}
                  >
                    {batchUploading ? "Running stacking classifier..." : "Run Underwrite Batch"}
                  </button>
                </div>

                {/* Templates box */}
                <div className="glass-panel p-6 bg-emerald-50/30 dark:bg-emerald-950/10 border border-emerald-100 dark:border-forest-800/20">
                  <h3 className="text-xs font-bold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Info size={14} />
                    Testing CSV Template
                  </h3>
                  
                  <pre className="mt-3 p-3 bg-gray-100 dark:bg-forest-950 rounded-2xl text-[9px] font-mono overflow-x-auto text-gray-600 dark:text-slate-350 leading-normal">
                    business_id,business_name,category,city<br />
                    BUS_0001,Amit Gym,Gym,Delhi<br />
                    BUS_0010,Sonia Salon,Salon,Bengaluru<br />
                    BUS_0025,Central Cafe,Cafe,Mumbai<br />
                    BUS_0100,Ganesh Provision,Retail,Pune
                  </pre>
                </div>
              </div>

              {/* Right pane: Scored CSV list */}
              <div className="lg:col-span-7 flex flex-col gap-6">
                <div className="glass-panel p-6 flex-1 flex flex-col min-h-[400px]">
                  <h2 className="font-outfit font-bold text-base text-[#0F2A21] mb-4 dark:text-white">Batch credit risk assessment report</h2>
                  
                  {!batchResults ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400 py-12">
                      <Building size={48} className="text-gray-300 mb-3" />
                      <span className="text-xs font-bold">Ready for scoring</span>
                      <p className="text-[10px] text-gray-400 mt-1 max-w-xs leading-relaxed">
                        Upload a merchant details CSV. Scored records with their risk classification will display here.
                      </p>
                    </div>
                  ) : (
                    <div className="flex-1 flex flex-col justify-between">
                      <div className="overflow-x-auto max-h-80 overflow-y-auto">
                        <table className="w-full text-left border-collapse text-[10px]">
                          <thead>
                            <tr className="border-b border-gray-200 dark:border-forest-900/20 text-gray-400 font-bold uppercase">
                              <th className="py-2.5">ID</th>
                              <th className="py-2.5">Business Name</th>
                              <th className="py-2.5">Category</th>
                              <th className="py-2.5">Score</th>
                              <th className="py-2.5">Risk Tier</th>
                            </tr>
                          </thead>
                          <tbody>
                            {batchResults.results.map((res, idx) => {
                              const colors = getRiskColor(res.risk_tier)
                              return (
                                <tr key={idx} className="border-b border-gray-50/50 dark:border-forest-900/10 hover:bg-[#F4F7F5]/50 dark:hover:bg-[#0e221b]/35 transition-colors">
                                  <td className="py-3 font-mono font-bold text-gray-405 dark:text-gray-400">{res.business_id}</td>
                                  <td className="py-3 font-bold text-[#0F2A21] dark:text-slate-100">{res.business_name}</td>
                                  <td className="py-3 font-medium text-gray-600 dark:text-slate-300">{res.category}</td>
                                  <td className="py-3 font-bold text-[#0F2A21] dark:text-slate-100">{res.credit_score}</td>
                                  <td className="py-3">
                                    <span className={`px-2.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${colors.bg} ${colors.text}`}>
                                      {colors.label}
                                    </span>
                                  </td>
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>

                      <div className="mt-6 pt-4 border-t border-gray-100 dark:border-forest-900/20 flex items-center justify-between text-xs">
                        <span className="text-gray-400 font-medium">Successfully processed {batchResults.total_scored} rows</span>
                        <button 
                          onClick={() => {
                            const headers = "business_id,business_name,category,city,credit_score,risk_tier\n"
                            const rows = batchResults.results.map(r => `${r.business_id},"${r.business_name}",${r.category},${r.city},${r.credit_score},"${r.risk_tier}"`).join("\n")
                            const blob = new Blob([headers + rows], { type: 'text/csv' })
                            const url = window.URL.createObjectURL(blob)
                            const a = document.createElement('a')
                            a.setAttribute('href', url)
                            a.setAttribute('download', `credit_scores_${Date.now()}.csv`)
                            a.click()
                          }}
                          className="bg-[#0F2A21] dark:bg-emerald-500 hover:bg-[#1C4E3D] text-white text-[10px] font-bold px-4 py-2.5 rounded-xl transition-all shadow-sm cursor-pointer"
                        >
                          Download Scored CSV
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* 4. MODEL EVALUATION VIEW */}
          {/* ========================================================================= */}
          {view === 'metrics' && (
            <div className="space-y-8 animate-fadeIn">
              
              {/* Row 1: Tuning parameters & model breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                {/* Left side explanation details */}
                <div className="lg:col-span-5 glass-panel p-6 flex flex-col justify-between">
                  <div>
                    <h2 className="font-outfit font-bold text-base text-[#0F2A21] border-b border-gray-100 dark:border-forest-900/20 pb-3 mb-3 dark:text-white">
                      Alternative Credit Underwriting model (v1.0.0)
                    </h2>
                    
                    <div className="space-y-4 text-xs leading-relaxed text-gray-500 dark:text-slate-300">
                      <p>
                        This model is a **Stacking Classifier Ensemble** that leverages multi-dimensional digital signals to evaluate small business creditworthiness.
                      </p>
                      
                      <div className="p-3 bg-gray-50 dark:bg-forest-950/40 rounded-xl space-y-1.5 font-medium text-gray-600 dark:text-slate-200 border border-gray-100 dark:border-forest-800/10">
                        <div className="flex justify-between"><span>Algorithm:</span><strong className="text-[#0F2A21] dark:text-emerald-400">Stacking Classifier</strong></div>
                        <div className="flex justify-between"><span>Base Estimators:</span><strong className="text-[#0F2A21] dark:text-emerald-400">XGBoost, LightGBM, RF, LogReg</strong></div>
                        <div className="flex justify-between"><span>Meta Classifier:</span><strong className="text-[#0F2A21] dark:text-emerald-400">Logistic Regression</strong></div>
                        <div className="flex justify-between"><span>Dataset size:</span><strong className="text-[#0F2A21] dark:text-emerald-400">800 micro-merchants</strong></div>
                      </div>

                      <p className="text-[10px] italic">
                        <strong>Note on target proxy:</strong> The model is optimized to predict 12-month business durability and growth. Real repayment outcome logs will replace this proxy variable once credit facilities are deployed.
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-3 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 text-[10px] text-emerald-800 dark:text-emerald-300 leading-normal flex items-start gap-2">
                    <Info size={16} className="shrink-0 mt-0.5" />
                    <span>
                      SHAP tree explanations are computed locally using the Random Forest classifier to satisfy regulatory explainability requirements.
                    </span>
                  </div>
                </div>

                {/* Right side metrics chart */}
                <div className="lg:col-span-7 glass-panel p-6 flex flex-col justify-between min-h-[340px]">
                  <div>
                    <h2 className="font-outfit font-bold text-base text-[#0F2A21] dark:text-white">Validation Set Comparison</h2>
                    <span className="text-xs text-gray-400 dark:text-gray-400 font-medium">Comparison of ROC-AUC and F1-Score metrics across models</span>
                  </div>

                  <div className="h-56 w-full mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={modelMetricsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? "#153b2f" : "#e6f2ed"} />
                        <XAxis dataKey="name" stroke="#94a3b8" tickLine={false} axisLine={false} tick={{ fontSize: 10, fontWeight: 500 }} />
                        <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} domain={[0.6, 0.95]} />
                        <Tooltip contentStyle={{ backgroundColor: darkMode ? '#0e221b' : '#ffffff', borderColor: darkMode ? '#153b2f' : '#e6f2ed', borderRadius: '16px' }} />
                        <Legend wrapperStyle={{ fontSize: 10, fontWeight: 600 }} />
                        <Bar name="ROC-AUC" dataKey="AUC" fill={darkMode ? "#a3d1bf" : "#0F2A21"} radius={[6, 6, 0, 0]} maxBarSize={20} />
                        <Bar name="F1-Score" dataKey="F1" fill="#10B981" radius={[6, 6, 0, 0]} maxBarSize={20} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

              </div>

              {/* Row 2: Metrics Table */}
              <div className="glass-panel p-6">
                <h3 className="font-outfit font-bold text-base text-[#0F2A21] mb-4 dark:text-white">Detailed Evaluation Metrics</h3>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-forest-900/20 text-gray-400 font-bold uppercase bg-gray-50/50 dark:bg-[#0e221b]/20">
                        <th className="px-4 py-3">Classification Model</th>
                        <th className="px-4 py-3">ROC-AUC (Out of Sample)</th>
                        <th className="px-4 py-3">Optimal F1-Score</th>
                        <th className="px-4 py-3">Brier Loss Calibration Score</th>
                        <th className="px-4 py-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-gray-100 dark:border-forest-900/10 hover:bg-[#F4F7F5]/30 dark:hover:bg-[#0e221b]/20">
                        <td className="px-4 py-3.5 font-bold text-[#0F2A21] dark:text-slate-100">Stacking Classifier (Champion)</td>
                        <td className="px-4 py-3.5 font-semibold text-emerald-700 dark:text-emerald-400">0.7964</td>
                        <td className="px-4 py-3.5 font-semibold">0.7841</td>
                        <td className="px-4 py-3.5 font-mono">0.1874</td>
                        <td className="px-4 py-3.5 text-right"><span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-400 font-bold rounded text-[9px] uppercase tracking-wider">Champion</span></td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-forest-900/10 hover:bg-[#F4F7F5]/30 dark:hover:bg-[#0e221b]/20">
                        <td className="px-4 py-3.5 font-medium">Random Forest Classifier</td>
                        <td className="px-4 py-3.5">0.7950</td>
                        <td className="px-4 py-3.5">0.7865</td>
                        <td className="px-4 py-3.5 font-mono">0.1905</td>
                        <td className="px-4 py-3.5 text-right"><span className="px-2 py-0.5 bg-gray-100 dark:bg-forest-900 text-gray-600 dark:text-slate-305 font-bold rounded text-[9px] uppercase tracking-wider">Candidate</span></td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-forest-900/10 hover:bg-[#F4F7F5]/30 dark:hover:bg-[#0e221b]/20">
                        <td className="px-4 py-3.5 font-medium">XGBoost Classifier</td>
                        <td className="px-4 py-3.5">0.7906</td>
                        <td className="px-4 py-3.5">0.7594</td>
                        <td className="px-4 py-3.5 font-mono">0.1942</td>
                        <td className="px-4 py-3.5 text-right"><span className="px-2 py-0.5 bg-gray-100 dark:bg-forest-900 text-gray-600 dark:text-slate-305 font-bold rounded text-[9px] uppercase tracking-wider">Candidate</span></td>
                      </tr>
                      <tr className="border-b border-gray-100 dark:border-forest-900/10 hover:bg-[#F4F7F5]/30 dark:hover:bg-[#0e221b]/20">
                        <td className="px-4 py-3.5 font-medium">LightGBM Classifier</td>
                        <td className="px-4 py-3.5">0.7890</td>
                        <td className="px-4 py-3.5">0.7709</td>
                        <td className="px-4 py-3.5 font-mono">0.1946</td>
                        <td className="px-4 py-3.5 text-right"><span className="px-2 py-0.5 bg-gray-100 dark:bg-forest-900 text-gray-600 dark:text-slate-305 font-bold rounded text-[9px] uppercase tracking-wider">Candidate</span></td>
                      </tr>
                      <tr className="hover:bg-[#F4F7F5]/30 dark:hover:bg-[#0e221b]/20">
                        <td className="px-4 py-3.5 font-medium">Regularized Logistic Regression</td>
                        <td className="px-4 py-3.5">0.7876</td>
                        <td className="px-4 py-3.5">0.7831</td>
                        <td className="px-4 py-3.5 font-mono">0.1928</td>
                        <td className="px-4 py-3.5 text-right"><span className="px-2 py-0.5 bg-gray-100 dark:bg-forest-900 text-gray-600 dark:text-slate-305 font-bold rounded text-[9px] uppercase tracking-wider">Baseline</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

        </main>
      </div>

    </div>
  )
}

export default App
