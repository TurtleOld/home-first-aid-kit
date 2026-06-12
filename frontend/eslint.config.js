import pluginVue from 'eslint-plugin-vue'
import vueEslintConfigPrettier from '@vue/eslint-config-prettier'

export default [
  {
    ignores: ['dist/**', 'dev-dist/**', 'node_modules/**']
  },
  ...pluginVue.configs['flat/recommended'],
  vueEslintConfigPrettier,
  {
    rules: {
      'vue/multi-word-component-names': 'off'
    }
  }
]
