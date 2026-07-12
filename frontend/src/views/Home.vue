<template>
  <main class="shell">
    <nav><strong>PILKQUANT</strong><span>NEWS INTELLIGENCE / RESEARCH ONLY</span></nav>
    <section class="hero">
      <p class="eyebrow">MARKET EVENT DECISION SUPPORT</p>
      <h1>Turn news into a<br><em>structured market view.</em></h1>
      <p class="lede">Upload source material, identify entities and narratives, simulate market-participant reactions, and produce an evidence-linked research report.</p>
      <div class="boundary">Advisory only — no order placement, trading execution, or promise of profitability.</div>
    </section>
    <section class="workflow">
      <article v-for="(step, index) in steps" :key="step.title"><b>0{{ index + 1 }}</b><h2>{{ step.title }}</h2><p>{{ step.body }}</p></article>
    </section>
    <section class="intake">
      <div><p class="eyebrow">START AN ANALYSIS</p><h2>Supply the event record</h2><p>PDF, Markdown, or text sources plus a research question.</p></div>
      <div class="form">
        <label class="drop">
          <input type="file" multiple accept=".pdf,.md,.txt" @change="selectFiles" />
          <span>{{ files.length ? files.map(file => file.name).join(', ') : 'Choose news source files' }}</span>
        </label>
        <textarea v-model="question" rows="5" placeholder="What assets may be affected, over what horizon, and where could the narrative reverse?" />
        <button :disabled="!ready" @click="startAnalysis">Analyze news →</button>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { setPendingUpload } from '../store/pendingUpload.js'

const router = useRouter()
const files = ref([])
const question = ref('')
const steps = [
  { title: 'Ingest news', body: 'Upload primary reporting, filings, transcripts, or analyst notes.' },
  { title: 'Map narratives', body: 'Extract entities, affected assets, claims, catalysts, and disagreement.' },
  { title: 'Simulate reactions', body: 'Reuse the participant graph and simulation engine to explore responses.' },
  { title: 'Report evidence', body: 'Return direction, confidence, horizon, reversal risk, and cited evidence.' }
]
const ready = computed(() => files.value.length > 0 && question.value.trim().length > 0)
const selectFiles = event => { files.value = Array.from(event.target.files) }
const startAnalysis = () => {
  if (!ready.value) return
  setPendingUpload(files.value, question.value.trim())
  router.push({ name: 'Process', params: { projectId: 'new' } })
}
</script>

<style scoped>
*{box-sizing:border-box}.shell{min-height:100vh;background:#f4f2eb;color:#151713;font-family:Inter,system-ui,sans-serif}nav{height:64px;padding:0 5vw;background:#151713;color:#fff;display:flex;align-items:center;justify-content:space-between;letter-spacing:.12em;font-size:.78rem}.hero{padding:9vw 8vw 6vw;max-width:1100px}.eyebrow{font:700 .72rem 'JetBrains Mono',monospace;letter-spacing:.18em;color:#d94b22}.hero h1{font-size:clamp(3rem,7vw,6.7rem);line-height:.94;letter-spacing:-.06em;margin:1rem 0 2rem}.hero em{font-weight:400;color:#d94b22}.lede{max-width:760px;font-size:1.3rem;line-height:1.6}.boundary{display:inline-block;margin-top:1.5rem;padding:.8rem 1rem;border:1px solid #151713;font:600 .75rem 'JetBrains Mono',monospace}.workflow{border-block:1px solid #bbb8ae;display:grid;grid-template-columns:repeat(4,1fr)}article{padding:2.5rem;border-right:1px solid #bbb8ae}article:last-child{border:0}article b{color:#d94b22;font-family:'JetBrains Mono'}article h2{font-size:1.2rem}.intake{padding:6vw 8vw;display:grid;grid-template-columns:1fr 1.4fr;gap:8vw}.intake h2{font-size:2.4rem}.form{display:grid;gap:1rem}.drop,textarea{background:#fff;border:1px solid #999;padding:1.2rem;font:inherit}.drop input{display:none}.drop{cursor:pointer}textarea{resize:vertical}button{background:#151713;color:#fff;border:0;padding:1.2rem;text-align:left;font-weight:700;cursor:pointer}button:disabled{opacity:.35;cursor:not-allowed}@media(max-width:800px){.workflow{grid-template-columns:1fr 1fr}.intake{grid-template-columns:1fr}nav span{display:none}}@media(max-width:500px){.workflow{grid-template-columns:1fr}article{border-right:0;border-bottom:1px solid #bbb8ae}}
</style>
