import { render, screen } from '@testing-library/react'
import { PackingProgress } from '@/components/PackingProgress'

describe('PackingProgress', () => {
  it('renders 0% when nothing is packed', () => {
    render(<PackingProgress packed={0} total={10} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.getByText('0 / 10 items packed')).toBeInTheDocument()
  })

  it('renders 100% when everything is packed', () => {
    render(<PackingProgress packed={5} total={5} />)
    expect(screen.getByText('100%')).toBeInTheDocument()
    expect(screen.getByText('5 / 5 items packed')).toBeInTheDocument()
  })

  it('renders correct percentage for partial packing', () => {
    render(<PackingProgress packed={3} total={4} />)
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('renders 0% when total is 0 (avoids division by zero)', () => {
    render(<PackingProgress packed={0} total={0} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('renders the progress bar element', () => {
    const { container } = render(<PackingProgress packed={2} total={4} />)
    const bar = container.querySelector('.bg-blue-500')
    expect(bar).toBeInTheDocument()
    expect(bar).toHaveStyle({ width: '50%' })
  })
})
