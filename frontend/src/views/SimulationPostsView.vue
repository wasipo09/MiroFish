<template>
  <main class="posts-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">PILKQUANT · MARKET REACTION</p>
        <h1>Simulation Posts</h1>
        <p class="simulation-id">{{ simulationId }}</p>
      </div>
      <div class="header-actions">
        <RouterLink class="button secondary" :to="`/market-reaction/${simulationId}/run`">
          Open dashboard
        </RouterLink>
        <button class="button" :disabled="loading" @click="loadPosts">
          {{ loading ? 'Refreshing…' : 'Refresh posts' }}
        </button>
      </div>
    </header>

    <section v-if="ready" class="summary" aria-live="polite">
      <strong>{{ posts.length }}</strong> visible posts
      <span>·</span>
      <span>English-only reading view</span>
    </section>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!ready && !loading" class="empty">
      Simulation posts will appear after the run and English normalization are complete.
    </p>
    <p v-else-if="loading && !posts.length" class="empty">Loading simulation posts…</p>
    <p v-else-if="!posts.length" class="empty">No posts are available for this simulation yet.</p>

    <section v-else class="feed" aria-label="Simulation post feed">
      <article v-for="post in posts" :key="post.post_id" class="post-card">
        <div class="post-meta">
          <span class="agent">Agent {{ post.user_id }}</span>
          <span>Post #{{ post.post_id }}</span>
          <span>Round {{ post.created_at }}</span>
        </div>
        <p class="content">{{ post.content }}</p>
        <blockquote v-if="post.quote_content">{{ post.quote_content }}</blockquote>
        <div class="engagement">
          <span>♥ {{ post.num_likes || 0 }}</span>
          <span>↗ {{ post.num_shares || 0 }}</span>
          <span>Reports {{ post.num_reports || 0 }}</span>
        </div>
      </article>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getRunStatusDetail, getSimulationPosts } from '../api/simulation'

const route = useRoute()
const simulationId = route.params.simulationId
const posts = ref([])
const loading = ref(false)
const error = ref('')
const ready = ref(false)

async function loadPosts() {
  loading.value = true
  error.value = ''
  try {
    const statusResponse = await getRunStatusDetail(simulationId)
    ready.value = statusResponse.data?.runner_status === 'completed'
    if (!ready.value) {
      posts.value = []
      return
    }
    const response = await getSimulationPosts(simulationId, 'twitter', 100, 0)
    posts.value = response.data?.posts || []
  } catch (requestError) {
    error.value = requestError?.message || 'Unable to load simulation posts.'
  } finally {
    loading.value = false
  }
}

onMounted(loadPosts)
</script>

<style scoped>
.posts-page { min-height: 100vh; padding: 40px; color: #e8edf5; background: #090d14; font-family: Inter, system-ui, sans-serif; }
.page-header { max-width: 960px; margin: 0 auto 24px; display: flex; align-items: end; justify-content: space-between; gap: 24px; }
.eyebrow { color: #64d8cb; font-size: 12px; letter-spacing: .16em; }
h1 { margin: 6px 0; font-size: clamp(32px, 5vw, 54px); }
.simulation-id { margin: 0; color: #8792a5; font-family: ui-monospace, monospace; }
.header-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.button { border: 0; border-radius: 8px; padding: 11px 16px; background: #64d8cb; color: #07110f; font-weight: 700; cursor: pointer; text-decoration: none; }
.button.secondary { background: #192130; color: #dbe5f3; }
.button:disabled { opacity: .6; cursor: wait; }
.summary, .feed, .error, .empty { max-width: 960px; margin-left: auto; margin-right: auto; }
.summary { margin-bottom: 18px; padding: 14px 16px; border: 1px solid #263247; border-radius: 10px; color: #aeb9ca; display: flex; gap: 8px; }
.feed { display: grid; gap: 14px; }
.post-card { padding: 20px; border: 1px solid #263247; border-radius: 12px; background: #111722; box-shadow: 0 12px 35px rgba(0,0,0,.16); }
.post-meta, .engagement { display: flex; gap: 14px; flex-wrap: wrap; color: #7f8ca1; font-size: 12px; }
.agent { color: #64d8cb; font-weight: 700; }
.content { margin: 14px 0; font-size: 17px; line-height: 1.65; }
blockquote { margin: 14px 0; padding: 12px 16px; border-left: 3px solid #64d8cb; background: #0b111b; color: #aeb9ca; }
.error { color: #ff8d8d; }
.empty { padding: 36px 0; color: #8792a5; }
@media (max-width: 720px) { .posts-page { padding: 24px 16px; } .page-header { align-items: start; flex-direction: column; } }
</style>
