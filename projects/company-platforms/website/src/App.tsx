import { Faq } from './components/Faq'
import { FinalCta } from './components/FinalCta'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { Hero } from './components/Hero'
import { Process } from './components/Process'
import { Services } from './components/Services'
import { StickyCta } from './components/StickyCta'
import { WorkflowMapper } from './components/WorkflowMapper'

export function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header />
      <main id="main">
        <Hero />
        <Services />
        <Process />
        <WorkflowMapper />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
      <StickyCta />
    </>
  )
}
