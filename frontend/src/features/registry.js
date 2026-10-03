const modules = import.meta.glob('./*/index.jsx', { eager: true })

export const features = Object.values(modules)
  .map((module) => module.default)
  .filter(Boolean)
  .sort((a, b) => (a.order ?? 99) - (b.order ?? 99))

export const enabledFeatures = (enabled = []) =>
  features.filter((feature) => enabled.includes(feature.flag))
