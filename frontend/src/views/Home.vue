<template>
  <main class="shell">
    <nav>
      <strong>PILKQUANT</strong>
      <div><a class="active" href="#analysis">News analysis</a><router-link :to="{ name: 'Process', params: { projectId: 'new' } }">Advanced market simulation</router-link></div>
    </nav>
    <section class="hero">
      <p class="eyebrow">MARKET EVENT DECISION SUPPORT</p>
      <h1>Turn news into a<br><em>structured market view.</em></h1>
      <p class="lede">Enter a headline, event detail, sources, affected assets, and research horizon. Receive a deterministic evidence-linked baseline for further research.</p>
      <div class="boundary">Advisory only — no order placement, trading execution, or promise of profitability.</div>
    </section>

    <section id="analysis" class="intake">
      <div><p class="eyebrow">PRIMARY WORKFLOW</p><h2>Analyze a news event</h2><p>This lexical baseline is a transparent research scaffold, not predictive analysis.</p></div>
      <form class="form" @submit.prevent="submitAnalysis">
        <label>Headline <span>{{ form.headline.length }}/300</span><input v-model.trim="form.headline" required maxlength="300" placeholder="Central bank signals slower rate cuts" /></label>
        <label>Content <span>{{ form.content.length }}/20,000</span><textarea v-model.trim="form.content" required maxlength="20000" rows="7" placeholder="Paste reporting, filing excerpts, transcript notes, or event context." /></label>
        <label>Sources <span>one per line, maximum 20</span><textarea v-model="sourcesText" required rows="4" placeholder="https://example.com/report&#10;filing:8-k" /></label>
        <label>Assets <span>comma-separated, optional, maximum 50</span><input v-model="assetsText" placeholder="US10Y, USD" /></label>
        <label>Horizon<select v-model="form.horizon" required><option v-for="item in horizons" :key="item" :value="item">{{ item }}</option></select></label>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button :disabled="loading || !ready">{{ loading ? 'Analyzing…' : 'Analyze news →' }}</button>
      </form>
    </section>

    <section v-if="result" class="result" aria-live="polite">
      <p class="eyebrow">STRUCTURED BASELINE</p><h2>{{ result.direction }} / {{ result.horizon }}</h2>
      <dl>
        <div><dt>Affected assets</dt><dd>{{ result.affected_assets.length ? result.affected_assets.join(', ') : 'Not specified' }}</dd></div>
        <div><dt>Confidence</dt><dd>{{ result.confidence }}</dd></div>
        <div><dt>Source count</dt><dd>{{ result.source_count }}</dd></div>
        <div><dt>Disagreement</dt><dd>{{ result.disagreement }}</dd></div>
        <div><dt>Reversal risk</dt><dd>{{ result.reversal_risk }}</dd></div>
        <div><dt>Advisory only</dt><dd>{{ result.advisory_only ? 'Yes' : 'No' }}</dd></div>
      </dl>
      <h3>Evidence</h3><ul><li v-for="item in result.evidence" :key="item">{{ item }}</li></ul>
      <p class="notice">{{ result.safety_notice }}</p>
    </section>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { analyzeNews } from '../api/news.js'

const horizons = ['intraday', '1-5d', '1-4w', '1-3m']
const form = reactive({ headline: '', content: '', horizon: '1-5d' })
const sourcesText = ref('')
const assetsText = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)
const parseSources = () => sourcesText.value.split('\n').map(value => value.trim()).filter(Boolean)
const parseAssets = () => assetsText.value.split(',').map(value => value.trim()).filter(Boolean)
const ready = computed(() => form.headline.length > 0 && form.content.length > 0 && parseSources().length > 0 && parseSources().length <= 20 && parseAssets().length <= 50 && parseSources().every(item => item.length <= 500) && parseAssets().every(item => item.length <= 50))

const submitAnalysis = async () => {
  if (!ready.value) { error.value = 'Check required fields and source/asset limits.'; return }
  loading.value = true; error.value = ''; result.value = null
  try {
    result.value = await analyzeNews({ ...form, sources: parseSources(), assets: parseAssets() })
  } catch (requestError) {
    error.value = requestError.response?.data?.message || requestError.message || 'Analysis failed.'
  } finally { loading.value = false }
}
</script>

<style scoped>
*{box-sizing:border-box}.shell{min-height:100vh;background:#f4f2eb;color:#151713;font-family:Inter,system-ui,sans-serif}nav{min-height:64px;padding:0 5vw;background:#151713;color:#fff;display:flex;align-items:center;justify-content:space-between;letter-spacing:.08em;font-size:.78rem}nav div{display:flex;gap:1.5rem}nav a{color:#bbb;text-decoration:none}.active,nav a:hover{color:#fff}.hero{padding:8vw 8vw 5vw;max-width:1100px}.eyebrow{font:700 .72rem 'JetBrains Mono',monospace;letter-spacing:.18em;color:#d94b22}.hero h1{font-size:clamp(3rem,7vw,6.7rem);line-height:.94;letter-spacing:-.06em;margin:1rem 0 2rem}.hero em{font-weight:400;color:#d94b22}.lede{max-width:760px;font-size:1.3rem;line-height:1.6}.boundary,.notice{display:inline-block;margin-top:1.5rem;padding:.8rem 1rem;border:1px solid #151713;font:600 .75rem 'JetBrains Mono',monospace}.intake{padding:5vw 8vw;display:grid;grid-template-columns:1fr 1.4fr;gap:8vw;border-top:1px solid #bbb8ae}.intake h2,.result h2{font-size:2.4rem}.form{display:grid;gap:1rem}.form label{display:grid;gap:.4rem;font-weight:700}.form label span{font-size:.72rem;color:#666;font-weight:400}.form input,.form textarea,.form select{background:#fff;border:1px solid #999;padding:1rem;font:inherit;width:100%}.form textarea{resize:vertical}.form button{background:#151713;color:#fff;border:0;padding:1.2rem;text-align:left;font-weight:700;cursor:pointer}.form button:disabled{opacity:.35;cursor:not-allowed}.error{color:#a52616}.result{margin:0 8vw 6vw;padding:3rem;background:#fff;border:1px solid #999}.result dl{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#bbb}.result dl div{background:#fff;padding:1rem}.result dt{font-size:.75rem;text-transform:uppercase;color:#666}.result dd{margin:.5rem 0 0;font-weight:700}.result h3{margin-top:2rem}.result ul{padding-left:1.5rem}.notice{display:block}@media(max-width:800px){.intake{grid-template-columns:1fr}.result dl{grid-template-columns:1fr 1fr}nav{align-items:flex-start;padding-block:1rem;gap:1rem}nav div{flex-direction:column;gap:.4rem}}@media(max-width:500px){.result dl{grid-template-columns:1fr}}
</style>
