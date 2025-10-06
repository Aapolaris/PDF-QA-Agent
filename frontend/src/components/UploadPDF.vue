<template>
  <div class="upload">
    <h2>Upload PDF</h2>
    <input type="file" @change="onFileChange" accept="application/pdf" />
    <button @click="uploadFile" :disabled="!file">Upload</button>
    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UploadPdf',              // <-- multi-word name fixes the linter error
  data() {
    return {
      file: null,
      message: ''
    }
  },
  methods: {
    onFileChange(e) {
      this.file = e.target.files[0]
      this.message = ''
    },
    async uploadFile() {
      if (!this.file) {
        this.message = 'Please select a PDF.'
        return
      }
      const formData = new FormData()
      formData.append('file', this.file)

      try {
        const res = await axios.post('http://localhost:5000/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.message = res.data.message || 'Uploaded successfully'
      } catch (err) {
        this.message = err.response?.data?.error || err.message
      }
    }
  }
}
</script>

<style scoped>
.upload { max-width: 520px; margin: 1rem; }
</style>
