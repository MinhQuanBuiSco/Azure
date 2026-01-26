import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, BarChart3, Brain, FileText, Zap } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Card, CardContent } from '../components/ui/card'

const features = [
  {
    icon: Brain,
    title: 'Multi-Agent AI',
    description: 'Powered by specialized AI agents working together for comprehensive analysis',
    color: 'blue',
  },
  {
    icon: BarChart3,
    title: 'Real-time Financial Data',
    description: 'Live market data, financial metrics, and historical price analysis',
    color: 'green',
  },
  {
    icon: FileText,
    title: 'Professional Reports',
    description: 'Generate institutional-quality research reports with actionable insights',
    color: 'purple',
  },
  {
    icon: Zap,
    title: 'Fast & Efficient',
    description: 'Get comprehensive research in minutes, not hours',
    color: 'yellow',
  },
]

export default function Home() {
  return (
    <div className="py-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-16"
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm text-muted-foreground">AI-Powered Research Pipeline</span>
        </div>

        <h1 className="text-5xl font-bold mb-6">
          <span className="gradient-text">Finance Research</span>
          <br />
          <span className="text-white">Made Intelligent</span>
        </h1>

        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          Harness the power of multi-agent AI to generate comprehensive financial
          research reports in minutes. Analyze companies, markets, and trends with
          institutional-grade insights.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Button asChild size="lg">
            <Link to="/research">
              <Sparkles className="w-5 h-5 mr-2" />
              Start Research
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link to="/reports">
              View Reports
            </Link>
          </Button>
        </div>
      </motion.div>

      {/* Features Grid */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16"
      >
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
          >
            <Card className="h-full hover:border-white/20 transition-all duration-300 group">
              <CardContent className="pt-6">
                <div className={`w-12 h-12 rounded-xl bg-${feature.color}-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className={`w-6 h-6 text-${feature.color}-400`} />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* How It Works */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="glass-card p-8 rounded-2xl"
      >
        <h2 className="text-2xl font-bold text-white mb-8 text-center">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {[
            { step: '1', title: 'Enter Company', desc: 'Provide a company name or ticker symbol' },
            { step: '2', title: 'AI Research', desc: 'Our agents gather data from multiple sources' },
            { step: '3', title: 'Analysis', desc: 'Deep analysis of financials, news, and market position' },
            { step: '4', title: 'Report', desc: 'Get a comprehensive, actionable research report' },
          ].map((item, index) => (
            <div key={item.step} className="text-center relative">
              <div className="w-12 h-12 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center mx-auto mb-4">
                <span className="text-primary font-bold">{item.step}</span>
              </div>
              <h3 className="font-semibold text-white mb-2">{item.title}</h3>
              <p className="text-sm text-muted-foreground">{item.desc}</p>
              {index < 3 && (
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-[2px] bg-gradient-to-r from-primary/50 to-transparent" />
              )}
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
