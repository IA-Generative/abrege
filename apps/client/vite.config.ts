import process from 'node:process'
import { fileURLToPath, URL } from 'node:url'

import {
  vueDsfrAutoimportPreset,
  vueDsfrComponentResolver,
} from '@gouvminint/vue-dsfr/meta'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'
import VueDevTools from 'vite-plugin-vue-devtools'

const env = loadEnv('', process.cwd(), '')

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  server: {
    port: Number(env.FRONT_PORT),
    strictPort: true,
    host: true,
    // host: '0.0.0.0',
    allowedHosts: true,
  },
  plugins: [
    vue(),
    vueJsx(),
    VueDevTools(),
    VitePWA({
      registerType: 'autoUpdate',
      selfDestroying: true,
      includeAssets: ['favicon.svg', 'safari-pinned-tab.svg'],
      workbox: {
        maximumFileSizeToCacheInBytes: 3000000,
        cleanupOutdatedCaches: true,
      },
      manifest: {
        name: 'Abrege',
        short_name: 'abrege',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        icons: [
          {
            src: '/android-chrome-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/android-chrome-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
        display: 'standalone',
      },
    }),
    AutoImport({
      include: [
        /\.[tj]sx?$/,
        /\.vue$/,
        /\.vue\?vue/,
      ],
      imports: [
        // @ts-expect-error TS2322
        'vue',
        // @ts-expect-error TS2322
        'vue-router',
        // @ts-expect-error TS2322
        'pinia',
        // @ts-expect-error TS2322
        'vitest',
        // @ts-expect-error TS2322
        vueDsfrAutoimportPreset,
      ],
      vueTemplate: true,
      dts: './src/auto-imports.d.ts',
      eslintrc: {
        enabled: true,
        filepath: './.eslintrc-auto-import.json',
        globalsPropValue: true,
      },
    }),
    Components({
      extensions: ['vue'],
      dirs: ['src/components'], // Autoimport de vos composants qui sont dans le dossier `src/components`
      include: [/\.vue$/, /\.vue\?vue/],
      dts: './src/components.d.ts',
      resolvers: [
        vueDsfrComponentResolver, // Autoimport des composants de VueDsfr dans les templates
      ],
    }),
    tailwindcss(),
  ],
  // base: process.env.BASE_URL || '/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
    dedupe: ['vue'],
  },
})
