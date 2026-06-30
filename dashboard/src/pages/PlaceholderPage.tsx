import './PlaceholderPage.css'

interface PlaceholderPageProps {
  icon: string
  title: string
  description: string
}

function PlaceholderPage({ icon, title, description }: PlaceholderPageProps) {
  return (
    <div className="placeholder-page">
      <span className="placeholder-page-icon">{icon}</span>
      <h1 className="placeholder-page-title">{title}</h1>
      <p className="placeholder-page-description">{description}</p>
      <span className="placeholder-page-badge">Coming Soon</span>
    </div>
  )
}

export default PlaceholderPage
