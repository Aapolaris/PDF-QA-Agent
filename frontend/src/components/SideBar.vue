<template>
  <div class="sidebar">
    <h2>📁 Documents</h2>

    <div class="upload-section">
      <input type="file" ref="fileInput" @change="onFileChange" accept="application/pdf" hidden />
      <button @click="$refs.fileInput.click()">+ Upload PDF</button>
      <p v-if="message" class="upload-message">{{ message }}</p>
    </div>

    <div class="chat-list">
      <div
        v-for="session in sessions"
        :key="session.session_id"
        :class="['chat-item', { active: session.session_id === currentSessionId }]"
        @click="$emit('select-session', session.session_id)" 
      >

        <div class="title"> 📄 {{ session.title || session.filename }}</div>
        <button class="delete-btn" @click.stop="$emit('delete-session', session.session_id)" title="Delete session">×</button>

      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios"

export default {
  name: "SideBar",
  props: {
    sessions: { type: Array, default: () => [] },
    currentSessionId: { type: String, default: null }
  },
  data() {
    return {
      message: ""
    }
  },
  methods: {
    async onFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      const formData = new FormData()
      formData.append("file", file)
      this.message = "Uploading..."
      try {
        const res = await axios.post("http://localhost:5000/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" }
        })
        
        console.log('SideBar - Upload response:', res.data); // 添加响应日志
        
        // 使用后端返回的 filename
        const sessionData = {
          session_id: res.data.session_id,
          filename: res.data.filename,  // 使用后端返回的 filename
          title: res.data.filename,  
          messages: []
        }
        
        console.log('SideBar - Emitting new session:', sessionData);
        
        this.$emit("new-session", sessionData)
        this.message = "✅ Upload succeeded"
      } catch (err) {
        console.error('SideBar - Upload error:', err);
        this.message = "❌ Upload failed: " + (err.response?.data?.error || err.message)
      }
      setTimeout(() => (this.message = ""), 3000)
      
      e.target.value = ''
    },

    // 在 SideBar.vue 的方法中添加
    async deleteSession(sessionId) {
      if (!confirm('Are you sure you want to delete this session?')) return
      
      try {
        await axios.post("http://localhost:5000/delete_session", {
          session_id: sessionId
        })
        // 发出事件让父组件处理
        this.$emit("delete-session", sessionId)
      } catch (error) {
        console.error('Failed to delete session:', error)
        alert('Failed to delete session')
      }
    }
  }
}
</script>

<style scoped>

.sidebar {
  width: 260px;
  height: 100%;
  background: #f4f5f7;
  padding: 1rem;
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
}

h2 {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  font-weight: bold;
}

.upload-section {
  margin-bottom: 3rem;
}

.upload-section button {
  width: 100%;
  padding: 0.6rem;
  background: rgb(53, 52, 52);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
}

.upload-message {
  font-size: 0.85rem;
  margin-top: 0.5rem;
  color: #333;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
}

.chat-item {
  display: flex;              /* 横向排列 */
  justify-content: space-between; /* 左右分布 */
  padding: 0.5rem;
  border-radius: 6px;
  background: #e6e7e9;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}
.chat-item.active {
  background: #1f65b4;
  color: white;
  font-weight: bold;
}
.chat-item:hover {
  background: #5398e7;
}

.title {
  font-size: 0.90rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 删除按钮样式 */
.delete-btn {
  background: transparent;
  border: none;
  color: #888;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 0.4rem;
  transition: color 0.2s ease, transform 0.2s ease;
}

.delete-btn:hover {
  color: #e74c3c;             /* 悬停变红 */
  transform: scale(1.2);      /* 悬停放大一点 */
}
</style>
