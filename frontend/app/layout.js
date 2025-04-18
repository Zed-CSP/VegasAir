import './globals.css'

export const metadata = {
  title: 'VegasAir - Airline Booking',
  description: 'Dynamic airline booking simulation',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <main className="container">
          {children}
        </main>
      </body>
    </html>
  )
}
