<template>
  <div class="main-container">
    <SideBar
      :sessions="sessions"
      :currentSessionId="currentSessionId" 
      @new-session="addSession"
      @select-session="selectSession"
      @delete-session="deleteSession"
    />
    <div class="right-panel">
      <div class="chat-header">
        <h3 class="title">{{ currentSession ? currentSession.title : 'No document loaded' }}</h3>
        <div v-if="currentSession" class="meta">Messages: {{ currentSession.messages.length }}</div>
      </div>

      <ChatPanel
        v-if="currentSession"
        :session="currentSession"
        :loading="loading"
        @send-message="handleSendQuestion"
      />

      <div v-else class="empty-state">
        <p>Upload a pdf / doc / markdown on the left to start a chat.</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios"
import SideBar from "../components/SideBar.vue"
import ChatPanel from "../components/ChatPanel.vue"

export default {
  name: "HomeView",
  components: { SideBar, ChatPanel },
  data() {
    return {
      sessions: [],
      currentSessionId: null,
      loading: false
    }
  },
  computed: {
    currentSession() {
      return this.sessions.find(s => s.session_id === this.currentSessionId) || null
    }
  },
  // created() {
  //   const raw = localStorage.getItem("pdf_sessions_v1")
  //   if (raw) {
  //     try {
  //       this.sessions = JSON.parse(raw)
  //       if (this.sessions.length) this.currentSessionId = this.sessions[0].session_id
  //     } catch (e) { console.log(e) }
  //   }
  // },
  async created() {
    // 先尝试从后端获取会话列表
    try {
        const res = await axios.get("http://localhost:5000/sessions")
        if (res.data.sessions && res.data.sessions.length > 0) {
          // 使用后端返回的会话
          this.sessions = res.data.sessions.map(s => ({
            session_id: s.session_id,
            title: s.filename,
            filename: s.filename,
            messages: Array(s.messages || 0).fill({}) // 简化处理
          }))
          if (this.sessions.length) this.currentSessionId = this.sessions[0].session_id
        } else {
          // 后端没有会话，回退到本地存储
          this.loadFromLocalStorage()
        }
      } catch (error) {
        console.error('Failed to load sessions from backend:', error)
        // 回退到本地存储
        this.loadFromLocalStorage()
      }
  },

  methods: {
    addSession(session) {
      console.log('Home.vue - Adding session:', session);
      this.sessions.unshift(session);
      this.currentSessionId = session.session_id;
      this.persist();
      
      // 调试日志
      console.log('Home.vue - Sessions after add:', this.sessions);
      console.log('Home.vue - Current session ID:', this.currentSessionId);
    },

    selectSession(id) {
      console.log('Home.vue - Selecting session:', id);
      this.currentSessionId = id;
    },

    persist() {
      localStorage.setItem("pdf_sessions_v1", JSON.stringify(this.sessions))
    },

    // 本地存储历史会话
    loadFromLocalStorage() {
      const raw = localStorage.getItem("pdf_sessions_v1")
      if (raw) {
        try {
          this.sessions = JSON.parse(raw)
          if (this.sessions.length) this.currentSessionId = this.sessions[0].session_id
        } catch (e) { console.log(e) }
      }
    },

    // 处理发送问题 - 修复参数
    async handleSendQuestion(payload) {  // 修复：现在接收对象而不是字符串
      if (!this.currentSession) return
      const session = this.currentSession

      // 立即添加用户消息（乐观更新）
      session.messages.push({ role: "user", content: payload.question })
      this.persist()

      // 使用 session_id 进行 API 调用
      const body = { 
        question: payload.question,
        session_id: session.session_id
      }

      this.loading = true
      try {
        const res = await axios.post("http://localhost:5000/ask", body)
        const assistantText = res.data.answer || res.data.final_answer || "No answer."
        session.messages.push({ role: "assistant", content: assistantText })
      } catch (err) {
        const msg = err.response?.data?.error || err.message || "Unknown error"
        session.messages.push({ role: "assistant", content: `❌ Error: ${msg}` })
      } finally {
        this.loading = false
        this.persist()
      }
    },

    // 在 Home.vue 的方法中添加
    async deleteSession(sessionId) {
      console.log('Home.vue - Deleting session:', sessionId);
      
      try {
        // 向后端发送删除请求
        await axios.post("http://localhost:5000/delete_session", {
          session_id: sessionId
        });
        
        // 从前端状态中移除会话
        this.sessions = this.sessions.filter(s => s.session_id !== sessionId);
        
        // 如果删除的是当前会话，重置当前会话ID
        if (this.currentSessionId === sessionId) {
          this.currentSessionId = this.sessions.length > 0 ? this.sessions[0].session_id : null;
        }
        
        // 更新本地存储
        this.persist();
        
        console.log('Home.vue - Session deleted successfully');
      } catch (error) {
          console.error('Home.vue - Failed to delete session:', error);
          alert('Failed to delete session: ' + (error.response?.data?.error || error.message));
        }
    }
  }
}
</script>

<style scoped>
.main-container {
  display: flex;
  height: 100%;
  overflow: hidden;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid #ececec;
  background: #fafafa;
}
.title {
  font-size: 1rem;
  margin: 0;
  max-width: 60%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.meta {
  font-size: 0.85rem;
  color: #666;
}
.empty-state {
  display:flex;
  align-items:center;
  justify-content:center;
  height: calc(100vh - 64px);
  color: #666;
}
</style>
