<style>
    .gallery-card {
        border: 2px solid var(--md-default-fg-color--lightest);
        border-radius: 8px;
        padding: 16px;
        margin: 24px 0;
    }

    .gallery-viewer {
        max-width: 600px;
        margin: 0 auto;
    }

    .gallery-viewer img {
        width: 100%;
        border-radius: 6px;
    }

    .gallery-label {
        text-align: center;
        font-weight: 600;
        margin: 8px 0;
    }

    .gallery-credit {
        text-align: left;
        font-size: 14px;
    }

    input[type="range"] {
        width: 100%;
        margin: 0 auto;
        accent-color: var(--md-primary-fg-color);
    }
</style>


# Gallery

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="galleryBathroomImage" src="../assets/gallery/bathroom.png">
    </div>
    <p class="gallery-credit">Bathroom scene "Salle de bain" courtesy of nacimus and Benedikt Bitterli, license CC BY 3.0. (Model downloaded from Benedikt Bitterli's Rendering Resources https://benedikt-bitterli.me/resources/.)</p>
</div>

## Auxiliary Buffers

### Combined

The following combined image will be used as reference for the auxiliary buffers below:

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="auxiliaryCombinedImage" src="../assets/gallery/Auxiliary_Buffers/combined.png">
    </div>
    <p class="gallery-credit">Kitchen scene courtesy of Jay-Artist and Benedikt Bitterli, license CC BY 3.0. (Model downloaded from Benedikt Bitterli's Rendering Resources https://benedikt-bitterli.me/resources/.)</p> 
</div>>

### Albedo

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="auxiliaryAlbedoImage" src="../assets/gallery/Auxiliary_Buffers/albedo.png">
    </div>
    <p class="gallery-credit">Kitchen scene courtesy of Jay-Artist and Benedikt Bitterli, license CC BY 3.0. (Model downloaded from Benedikt Bitterli's Rendering Resources https://benedikt-bitterli.me/resources/.)</p> 
</div>

### Normal

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="auxiliaryNormalImage" src="../assets/gallery/Auxiliary_Buffers/normal.png">
    </div>
    <p class="gallery-credit">Kitchen scene courtesy of Jay-Artist and Benedikt Bitterli, license CC BY 3.0. (Model downloaded from Benedikt Bitterli's Rendering Resources https://benedikt-bitterli.me/resources/.)</p> 
</div>

### Roughness

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="auxiliaryRoughnessImage" src="../assets/gallery/Auxiliary_Buffers/roughness.png">
    </div>
    <p class="gallery-credit">Kitchen scene courtesy of Jay-Artist and Benedikt Bitterli, license CC BY 3.0. (Model downloaded from Benedikt Bitterli's Rendering Resources https://benedikt-bitterli.me/resources/.)</p> 
</div>

### Metallic

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="auxiliaryMetallicImage" src="../assets/gallery/Auxiliary_Buffers/metallic.png">
    </div>
    <p class="gallery-credit">Kitchen scene courtesy of Jay-Artist and Benedikt Bitterli, license CC BY 3.0. (Model downloaded from Benedikt Bitterli's Rendering Resources https://benedikt-bitterli.me/resources/.)</p> 
</div>

## Denoising

Please note that this denoiser prototype is not a great denoiser because of the limited amount of produceable scene variety. On other scenes, there may be noticeable artifacts and issues because of the lack of variety and the missing variance and gradient buffers from Bako et al's implementation. However, the image below represents a scene where the denoiser performs well. They were both rendered at 100 samples:

### Noisy

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="denoisingNoisyImage" src="../assets/gallery/Denoising/noisy.png">
    </div>
</div>

### Denoised

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="denoisingDenoisedImage" src="../assets/gallery/Denoising/denoised.png">
    </div>
</div>

### Loss Graph

The KPCN network was trained with 300 pretrain epochs and 500 fine-tune epochs.

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="DenoisingLossGraphImage" src="../assets/gallery/Denoising/loss_graph.png">
    </div>
</div>

## Diffuse / Specular Split

### Combined

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDepthImage" src="../assets/gallery/Diffuse-Specular_Split/combined.png">
    </div>
    <p class="gallery-credit">Dragon model courtesy of XYZ RGB Inc. and the Stanford University Computer Graphics Laboratory.</p> 
</div>

### Diffuse

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDepthImage" src="../assets/gallery/Diffuse-Specular_Split/diffuse.png">
    </div>
    <p class="gallery-credit">Dragon model courtesy of XYZ RGB Inc. and the Stanford University Computer Graphics Laboratory.</p> 
</div>


### Specular

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDepthImage" src="../assets/gallery/Diffuse-Specular_Split/specular.png">
    </div>
    <p class="gallery-credit">Dragon model courtesy of XYZ RGB Inc. and the Stanford University Computer Graphics Laboratory.</p> 
</div>


## BVH Debug

The image below will be used as the reference image for the BVH debug images.

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDebugCombinedImage" src="../assets/gallery/BVH_Debug/combined_16384.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
</div>

### BVH Bounds

#### Layer

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhBoundsLayerImage" src="../assets/gallery/BVH_Debug/Bounds/Layer/layer_all.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
    <p class="gallery-label" id="bvhBoundsLayerLabel">Layer: All</p>
    <input type="range" id="bvhBoundsLayerSlider" min="-1" max="28" step="1" value="-1">
</div>

<script>
    const bvhBoundsLayerSlider = document.getElementById("bvhBoundsLayerSlider");
    const bvhBoundsLayerImage = document.getElementById("bvhBoundsLayerImage");
    const bvhBoundsLayerLabel = document.getElementById("bvhBoundsLayerLabel");

    bvhBoundsLayerSlider.addEventListener("input", function() {
        const layer = bvhBoundsLayerSlider.value;

        if (layer == -1) {
            bvhBoundsLayerImage.src = "../assets/gallery/BVH_Debug/Bounds/Layer/layer_all.png";
            bvhBoundsLayerLabel.textContent = "Layer: All";
        } else {
            bvhBoundsLayerImage.src = "../assets/gallery/BVH_Debug/Bounds/Layer/layer_" + layer + ".png";
            bvhBoundsLayerLabel.textContent = "Layer: " + layer;
        }
    });
</script>

#### Depth

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhBoundsDepthImage" src="../assets/gallery/BVH_Debug/Bounds/Depth/depth_max.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
    <p class="gallery-label" id="bvhBoundsDepthLabel">Depth: Max</p>
    <input type="range" id="bvhBoundsDepthSlider" min="-1" max="28" step="1" value="-1">
</div>

<script>
    const bvhBoundsDepthSlider = document.getElementById("bvhBoundsDepthSlider");
    const bvhBoundsDepthImage = document.getElementById("bvhBoundsDepthImage");
    const bvhBoundsDepthLabel = document.getElementById("bvhBoundsDepthLabel");

    bvhBoundsDepthSlider.addEventListener("input", function() {
        const depth = bvhBoundsDepthSlider.value;

        if (depth == -1) {
            bvhBoundsDepthImage.src = "../assets/gallery/BVH_Debug/Bounds/Depth/depth_max.png";
            bvhBoundsDepthLabel.textContent = "Depth: All";
        } else {
            bvhBoundsDepthImage.src = "../assets/gallery/BVH_Debug/Bounds/Depth/depth_" + depth + ".png";
            bvhBoundsDepthLabel.textContent = "Depth: " + depth;
        }
    });
</script>

### BVH Depth

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDepthImage" src="../assets/gallery/BVH_Debug/Depth/depth.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
</div>

### Disintegration

Now, what happens when the path tracer breaks out the BVH traversal after a certain maximum depth? Use the slider below to find out.

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDisintegrationImage" src="../assets/gallery/BVH_Debug/Disintegration/depth_32.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
    <p class="gallery-label" id="bvhDisintegrationLabel">Max Depth: 32</p>
    <div class="gallery-slider-row">
        <input type="range" id="bvhDisintegrationSlider" min="0" max="5" step="1" value="0">
        <span id="bvhDisintegrationSliderValue">32</span>
    </div>
</div>

<script>
    const bvhDisintegrationSlider = document.getElementById("bvhDisintegrationSlider");
    const bvhDisintegrationImage = document.getElementById("bvhDisintegrationImage");
    const bvhDisintegrationLabel = document.getElementById("bvhDisintegrationLabel");
    const sliderValueDisplay = document.getElementById("bvhDisintegrationSliderValue");

    const depthSteps = [32, 16, 8, 4, 2, 1];

    bvhDisintegrationSlider.addEventListener("input", function() {
        const index = bvhDisintegrationSlider.value;
        const depth = depthSteps[index];

        bvhDisintegrationImage.src = "../assets/gallery/BVH_Debug/Disintegration/depth_" + depth + ".png";
        bvhDisintegrationLabel.textContent = "Max Depth: " + depth;
        sliderValueDisplay.textContent = depth;
    });
</script>
