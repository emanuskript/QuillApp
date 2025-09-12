<template>
  <div class="seshat-hero">
    <!-- Moving icon background -->
    <div class="bg-icons" aria-hidden="true"></div>

    <!-- Centered Logo -->
    <div class="brand">
      <img src="@/assets/logo.png" alt="Seshat logo" />
    </div>

    <!-- Banner -->
    <section class="banner-card" role="region" aria-label="Start panel">
      <div class="ribbon">
        <span>Provide a link or upload an image</span>
      </div>

      <div class="form">
        <!-- IIIF Link Input -->
        <label class="field">
          <i class="fa-solid fa-link" aria-hidden="true"></i>
          <input
            type="text"
            v-model="iiifLink"
            :disabled="fileName !== ''"
            placeholder="Enter IIIF Link"
            aria-label="IIIF Link"
          />
        </label>

        <!-- Upload -->
        <div class="upload">
          <label class="upload-btn" for="upload-file">
            <i class="fa-solid fa-upload" aria-hidden="true"></i>
            <span>Upload Image</span>
          </label>
          <input
            id="upload-file"
            class="file-input"
            type="file"
            accept="image/*,application/pdf"
            @change="handleFileUpload"
          />
          <span class="file-name" :class="{ 'muted': !fileName }">
            {{ fileName || 'Supports: JPG, PNG, GIF, PDF, WebP, SVG' }}
          </span>
        </div>

        <!-- Start -->
        <button class="cta" @click="startAnnotating">
          <span>Start Annotating</span>
          <i class="fa-solid fa-arrow-right-long" aria-hidden="true"></i>
        </button>
      </div>

      <div class="base-accent" aria-hidden="true"></div>
    </section>
  </div>
</template>

<script>
export default {
  name: "SeshatInput",
  data() {
    return {
      iiifLink: "",
      fileName: "",
      imageSrc: "",
    };
  },
  methods: {
    handleFileUpload(e) {
      const file = e.target.files?.[0];
      if (!file) return;
      this.fileName = file.name;
      this.imageSrc = URL.createObjectURL(file);
      this.iiifLink = "";
    },
    isValidIIIFLink(link) {
      return !!link && link.startsWith("http");
    },
    startAnnotating() {
      if (!(this.iiifLink || this.fileName)) {
        alert("Please provide a valid IIIF link or upload an image.");
        return;
      }
      if (this.iiifLink && !this.isValidIIIFLink(this.iiifLink)) {
        alert("Please provide a valid IIIF link (must start with http…).");
        return;
      }
      const src = this.iiifLink || this.imageSrc;
      this.$router.push({ name: "IIIFViewer", params: { source: src } });
    },
  },
};
</script>

<style scoped>
/* --- Layout shell --- */
.seshat-hero {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: radial-gradient(
    1200px 600px at 50% -10%,
    #eef6ff 0%,
    #f6f9ff 40%,
    #f8fbff 60%,
    #f4f6fa 100%
  );
}

/* --- Animated icon background --- */
.bg-icons {
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='240' height='240' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%231b3e83' fill-opacity='.07'%3E%3Cpath d='M48 24h48v8H48zM32 88l24-14 24 14-24 14z'/%3E%3Ccircle cx='180' cy='40' r='10'/%3E%3Cpath d='M176 120h8v48h-8z'/%3E%3Cpath d='M84 160c0-11 9-20 20-20s20 9 20 20-9 20-20 20-20-9-20-20zm-36 44l30-8 8 30-30 8z'/%3E%3C/g%3E%3C/svg%3E");
  background-size: 240px 240px;
  animation: scroll-bg 20s linear infinite;
  pointer-events: none;
}
@keyframes scroll-bg {
  from {
    background-position: 0 0;
  }
  to {
    background-position: -240px -240px;
  }
}

/* --- Logo --- */
.brand {
  position: absolute;
  top: 40px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}
.brand img {
  height: 160px; /* Bigger logo */
  width: auto;
  filter: drop-shadow(0 8px 18px rgba(22, 45, 90, 0.2));
}

/* --- Banner --- */
.banner-card {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(780px, 92vw);
  background: #fffdfa;
  border: 1px solid #f2e3b3;
  border-radius: 18px;
  box-shadow: 0 14px 40px rgba(11, 39, 85, 0.12);
  padding: 24px;
}

.ribbon {
  --r: #2b6fde;
  margin: -18px auto 18px;
  width: 70%;
  background: var(--r);
  color: #fff;
  font-weight: 700;
  text-align: center;
  border-radius: 14px;
  padding: 10px 16px;
  letter-spacing: 0.2px;
  box-shadow: 0 6px 0 rgba(22, 69, 170, 0.25) inset;
}

.base-accent {
  position: absolute;
  left: 26px;
  right: 26px;
  bottom: -10px;
  height: 10px;
  border-radius: 10px;
  background: linear-gradient(90deg, #f6d684, #eac663);
  box-shadow: 0 6px 10px rgba(180, 140, 40, 0.25);
}

.form {
  display: grid;
  gap: 12px;
}

/* Input field */
.field {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f5f9ff;
  border: 1px solid #d7e6ff;
  border-radius: 10px;
  padding: 10px 12px;
}
.field i {
  color: #2b6fde;
}
.field input {
  flex: 1;
  font-size: 15px;
  border: 0;
  outline: 0;
  background: transparent;
  padding: 6px 4px;
  color: #0f2250;
}

/* Upload row */
.upload {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #eaf1ff;
  color: #1746b2;
  border: 1px solid #cfe0ff;
  border-radius: 10px;
  padding: 9px 14px;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s ease;
}
.upload-btn:hover {
  background: #e1ebff;
  transform: translateY(-1px);
}
.file-input {
  display: none;
}
.file-name {
  color: #334;
  font-size: 14px;
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-name.muted {
  color: #9099aa;
}

/* CTA */
.cta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #2b6fde;
  color: #fff;
  border: 1px solid #2059d5;
  border-radius: 12px;
  padding: 12px 16px;
  font-weight: 700;
  letter-spacing: 0.2px;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(23, 70, 178, 0.25);
  transition: transform 0.06s ease, filter 0.15s ease;
}
.cta:hover {
  filter: brightness(0.98);
}
.cta:active {
  transform: translateY(1px);
}
</style>
