<template>
  <div class="chat-panel">
    <div class="chat-window" ref="chatWindow">
      <!-- 添加 session 存在性检查 -->
      <div
        v-for="(msg, idx) in (session?.messages || [])"
        :key="idx"
        :class="['chat-message', msg.role === 'user' ? 'user' : 'assistant']"
      >
        <div class="bubble" v-html="renderMarkdown(msg.content)"></div>
      </div>

      <p v-if="loading" class="typing">🤖 Thinking...</p>
    </div>

    <div class="chat-input">
      <textarea
        v-model="question"
        placeholder="Ask anything about this PDF..."
        @keyup.enter.exact.prevent="onSend"
        rows="2"
        :disabled="!session" 
      ></textarea>
      <button @click="onSend" :disabled="loading || !question.trim() || !session">Send</button>
    </div>
  </div>
</template>

<script>
import { marked } from "marked"

export default {
  name: "ChatPanel",
  props: {
    session: { type: Object, default: null }, // 改为 default: null
    loading: { type: Boolean, default: false }
  },
  data() {
    return { question: "" }
  },
  methods: {
    renderMarkdown(text) {
      return marked(text || "")
    },
    onSend() {
      // 添加 session 检查
      if (!this.session || !this.question.trim()) return
      const q = this.question
      this.question = ""
      this.$emit("send-message", {
        session_id: this.session.session_id,
        question: q
      })
      this.$nextTick(this.scrollToBottom)
    },
    scrollToBottom() {
      const el = this.$refs.chatWindow
      if (el) el.scrollTop = el.scrollHeight
    }
  },
  mounted() {
    this.scrollToBottom()
  },
  watch: {
    session: {
      handler(newSession) {
        if (newSession) {
          this.$nextTick(this.scrollToBottom)
        }
      },
      deep: true
    }
  }
}
</script>

<style scoped>
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  position: relative;
  background: #f9fafb;
}

.chat-window {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  min-height: 0;
}

.chat-message {
  display: flex;
  margin-bottom: 0.6rem;
}
.chat-message.user {
  justify-content: flex-end;
}
.chat-message.assistant {
  justify-content: flex-start;
}

.bubble {
  display: inline-block;
  padding: 0rem 0.9rem;
  border-radius: 20px;
  line-height: 1.3;
  font-size: 0.95rem;
  background: #e5e7eb;
  color: #333;
  max-width: 70%;
  box-shadow: none;
}

.chat-message.user .bubble {
  background: #326298;
  color: #fff;
  border-bottom-right-radius: 3px;
}

.chat-message.assistant .bubble {
  background: #f3f4f6;
  color: #111827;
  border-bottom-left-radius: 3px;
}

.typing {
  font-style: italic;
  color: #555;
  margin: 0.3rem 0;
}

.chat-input {
  flex-shrink: 0;  /* 防止溢出，同时其父级、父级的父级...等要设置min-height为0 */
  display: flex;
  padding: 1.8rem 10rem;
  gap: 1.8em;
}

textarea {
  flex: 1;
  padding: 0.6rem 1rem;
  resize: none;
  border: 1px solid #ccc;
  border-radius: 20px;
  font-size: 0.95rem;
  line-height: 1.4;
  outline: none;
  height: 1.5em;
}

button {
  margin-left: 0.6rem;
  padding: 0rem 1.2rem;
  background: rgb(53, 52, 52);
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.95rem;
}

button:disabled {
  background: #6f6f6f;
}
</style>
