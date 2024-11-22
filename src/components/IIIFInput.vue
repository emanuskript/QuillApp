<template>
  <div class="container">
    <!-- Centered Logo -->
    <div class="logo">
      <img src="@/assets/logo.png" alt="Quill Logo" />
    </div>

    <!-- Input Section -->
    <div class="input-box">
      <h2>Please provide a link or upload an image to start using the tool.</h2>
      <div class="input-group">
        <!-- IIIF Link Input -->
        <div class="input-field">
          <label for="iiif-link">
            <i class="fas fa-link"></i>
          </label>
          <input
            type="text"
            id="iiif-link"
            v-model="iiifLink"
            :disabled="fileName !== ''"
            placeholder="Enter IIIF Link"
          />
        </div>

        <!-- File Upload Button -->
        <div class="upload-wrapper">
          <label class="upload-btn" for="upload-file">
            <i class="fas fa-upload"></i>
            Upload File
          </label>
          <input
            type="file"
            id="upload-file"
            @change="handleFileUpload"
            class="upload-input"
          />
          <span class="file-name">{{ fileName }}</span>
        </div>

        <!-- Start Annotating Button -->
        <button class="annotate-btn" @click="startAnnotating">
          Start Annotating <i class="fas fa-arrow-right"></i>
        </button>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  data() {
    return {
      iiifLink: "", // Stores the input IIIF link
      fileName: "", // Stores the uploaded file name
      imageSrc: "", // Source for the uploaded file
    };
  },
  methods: {
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.fileName = file.name;
        this.imageSrc = URL.createObjectURL(file); // Create a URL for the uploaded file
        this.iiifLink = ""; // Clear the IIIF link when a file is uploaded
        console.log("File uploaded:", this.imageSrc); // Debugging: check file URL
      }
    },
    startAnnotating() {
      if (this.iiifLink || this.fileName) {
        if (this.isValidIIIFLink(this.iiifLink)) {
          console.log("IIIF Link:", this.iiifLink); // Debugging: check the IIIF link before routing
          this.$router.push({
            name: "IIIFViewer",
            params: { source: this.iiifLink || this.imageSrc }, // Pass the correct value
          });
        } else if (this.fileName) {
          console.log("Image Source:", this.imageSrc); // Debugging: check image source before routing
          this.$router.push({
            name: "IIIFViewer",
            params: { source: this.imageSrc }, // Pass the file source
          });
        } else {
          alert("Please provide a valid IIIF link or upload an image.");
        }
      } else {
        alert("Please provide a valid IIIF link or upload an image.");
      }
    },
    isValidIIIFLink(link) {
      // Use basic validation for IIIF manifest (not restricted to '.json')
      return link.startsWith("http");
    },
  },
};
</script>


<style scoped>
/* Styling remains unchanged */
html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  background-color: #f1f1f1;
}

.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-width: 100vw;
  background-color: #f1f1f1;
  font-family: "Arial", sans-serif;
}

.logo {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
}

.logo img {
  width: 140px;
}

.input-box {
  background-color: #e3f2f9;
  border-radius: 10px;
  padding: 40px;
  width: 600px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.input-box h2 {
  font-size: 18px;
  font-weight: 400;
  color: #333;
  margin-bottom: 30px;
}

.input-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.input-field {
  display: flex;
  align-items: center;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 10px;
  width: 100%;
}

.input-field label {
  margin-right: 10px;
  font-size: 16px;
  color: #666;
}

.input-field input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  padding: 5px;
}

.upload-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  background-color: #f1f1f1;
  color: #e97a8a;
  border: 1px solid #e97a8a;
  border-radius: 5px;
  padding: 10px 15px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.upload-btn:hover {
  background-color: #e97a8a;
  color: #fff;
}

.file-name {
  font-size: 14px;
  color: #666;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.annotate-btn {
  background-color: #f1f1f1;
  color: #e97a8a;
  border: 1px solid #e97a8a;
  padding: 10px 20px;
  font-size: 16px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.annotate-btn:hover {
  background-color: #e97a8a;
  color: #fff;
}
</style>
