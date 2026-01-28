import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Plane,
  Hotel,
  Sun,
  MapPin,
  Utensils,
  DollarSign,
  ArrowRight,
  Sparkles,
} from 'lucide-react'

const features = [
  {
    icon: Plane,
    title: 'Flight Search',
    description: 'Find the best flights across major airlines',
    iconClass: 'icon-cyan',
  },
  {
    icon: Hotel,
    title: 'Hotels',
    description: 'Discover perfect accommodations for any budget',
    iconClass: 'icon-violet',
  },
  {
    icon: Sun,
    title: 'Weather',
    description: 'Get accurate forecasts and packing tips',
    iconClass: 'icon-amber',
  },
  {
    icon: MapPin,
    title: 'Attractions',
    description: 'Explore must-see places and hidden gems',
    iconClass: 'icon-emerald',
  },
  {
    icon: Utensils,
    title: 'Restaurants',
    description: 'Find local cuisine and dining experiences',
    iconClass: 'icon-rose',
  },
  {
    icon: DollarSign,
    title: 'Budget',
    description: 'Calculate trip costs and manage expenses',
    iconClass: 'icon-lime',
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15,
    },
  },
}

export default function Home() {
  return (
    <div className="w-full flex flex-col gap-16">
      {/* Hero Section - spans full width, text centered */}
      <section className="w-full pt-8 md:pt-12">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
          className="w-full text-center space-y-6"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-subtle"
          >
            <Sparkles className="w-4 h-4 text-accent" />
            <span className="text-sm text-muted">
              Powered by MCP
            </span>
          </motion.div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-balance">
            <span className="text-gradient">AI-Powered</span>
            <br />
            <span className="text-foreground">Travel Planning</span>
          </h1>

          {/* Description */}
          <p className="text-lg md:text-xl text-muted text-balance leading-relaxed">
            Plan your perfect trip with intelligent recommendations for flights,
            hotels, attractions, and more. Let AI handle the research while you dream.
          </p>

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="pt-2"
          >
            <Link to="/planner" className="btn-primary text-base">
              Start Planning
              <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="w-full">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="features-grid"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={itemVariants}
              className="feature-card group"
            >
              <div className={`feature-icon ${feature.iconClass}`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-muted leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* How It Works */}
      <section className="w-full">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="glass-card p-8 md:p-12"
        >
          <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-10 text-center">
            How It Works
          </h2>

          <div className="grid md:grid-cols-3 gap-8 md:gap-12">
            {[
              {
                step: '01',
                title: 'Enter Destination',
                desc: 'Tell us where you want to go and when',
              },
              {
                step: '02',
                title: 'AI Research',
                desc: 'Our AI searches for the best options across multiple sources',
              },
              {
                step: '03',
                title: 'Get Results',
                desc: 'Receive personalized itinerary with all details',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15, duration: 0.5 }}
                className="text-center"
              >
                <div className="text-5xl md:text-6xl font-bold text-gradient mb-4">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {item.title}
                </h3>
                <p className="text-sm text-muted">
                  {item.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>
    </div>
  )
}
