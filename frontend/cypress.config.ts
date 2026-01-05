// C:\Users\Vinay\Project\frontend\cypress.config.ts

import { defineConfig } from 'cypress'
import dotenv from 'dotenv'
import path from 'path'

export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      console.log('--- Loading Cypress Config ---')

      const envFile = process.env.ENV_FILE || '.env.cy.local'
      console.log(`[DEBUG] ENV_FILE variable from npm script is: ${envFile}`)

      const envFilePath = path.resolve(process.cwd(), envFile)
      console.log(`[DEBUG] Attempting to load .env file from path: ${envFilePath}`)

      const envConfig = dotenv.config({ path: envFilePath, override: false })

      if (envConfig.error) {
        console.error('[DEBUG] ERROR loading .env file:', envConfig.error)
      } else {
        console.log('[DEBUG] Successfully loaded .env file. Parsed variables:', envConfig.parsed)
      }

      if (envConfig.parsed) {
        // This line loads ALL variables from your .env file into Cypress.
        // It's the most important one.
        config.env = { ...config.env, ...envConfig.parsed }

        // This line correctly sets the baseUrl.
        config.baseUrl = envConfig.parsed.CYPRESS_BASE_URL || config.baseUrl
      }

      console.log('[DEBUG] Final Cypress config.env object:', config.env)
      console.log(`[DEBUG] Final baseUrl is: ${config.baseUrl}`)
      console.log('----------------------------')

      return config
    },
  },
})
