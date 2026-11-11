const fallbackCharacters = [
  {
    id: "lina",
    name: "Lina",
    consistency_percent: 92,
    identity_strength: 0.85,
    style: { preset: "cinematic" },
    style_labels: ["电影人像", "柔和日光", "50mm 镜头"],
    memory_labels: ["清晨咖啡馆", "雨夜街道", "棚拍头像"],
    prompt: "一个年轻的亚洲女性，柔和的自然光，户外公园，微风吹动头发，清新自然的氛围，写真摄影风格，50mm 镜头，浅景深",
  },
  {
    id: "kira",
    name: "Kira",
    consistency_percent: 87,
    identity_strength: 0.78,
    style: { preset: "anime" },
    style_labels: ["动漫", "干净线条", "柔和辉光"],
    memory_labels: ["学校天台", "城市霓虹", "春日花园"],
    prompt: "动漫风格角色，清晨街角，柔和轮廓光，轻微微笑，干净饱和色彩，半身构图",
  },
  {
    id: "alex",
    name: "Alex",
    consistency_percent: 89,
    identity_strength: 0.82,
    style: { preset: "commercial" },
    style_labels: ["商业大片", "棚拍主光", "品牌广告"],
    memory_labels: ["棚拍广告", "产品发布", "户外海报"],
    prompt: "商业广告模特，极简摄影棚，品牌大片质感，受控主光，中景构图，清晰面部结构",
  },
];

const fallbackLoras = [
  {
    id: "portrait-consistency",
    name: "Portrait Consistency LoRA",
    label: "人像一致性",
    preset: "cinematic",
    default_weight: 0.72,
    description: "锁定人像脸型、五官结构和自然肤色。",
  },
  {
    id: "soft-daylight-pro",
    name: "Soft Daylight Pro LoRA",
    label: "柔和日光",
    preset: "cinematic",
    default_weight: 0.58,
    description: "控制户外自然光、浅景深和柔和肤色。",
  },
  {
    id: "anime-clean-line",
    name: "Anime Clean Line LoRA",
    label: "动漫线稿",
    preset: "anime",
    default_weight: 0.64,
    description: "控制干净动漫线条和角色脸部稳定性。",
  },
  {
    id: "brand-campaign",
    name: "Brand Campaign LoRA",
    label: "商业广告",
    preset: "commercial",
    default_weight: 0.62,
    description: "控制品牌广告棚拍质感和商业布光。",
  },
  {
    id: "campaign-poster",
    name: "Campaign Poster LoRA",
    label: "商业海报",
    preset: "commercial",
    default_weight: 0.64,
    description: "控制海报主视觉、中心产品构图和高光反射质感。",
  },
  {
    id: "editorial-illustration",
    name: "Editorial Illustration LoRA",
    label: "插画质感",
    preset: "cinematic",
    default_weight: 0.6,
    description: "控制纸纹、笔触和编辑海报色彩。",
  },
  {
    id: "render-3d-polish",
    name: "3D Render Polish LoRA",
    label: "3D 材质",
    preset: "cinematic",
    default_weight: 0.56,
    description: "控制 3D 材质、软箱灯和渲染高光。",
  },
  {
    id: "drama-still",
    name: "Drama Still LoRA",
    label: "剧照光影",
    preset: "cinematic",
    default_weight: 0.62,
    description: "控制低照度剧照、冷暖对比和叙事镜头。",
  },
  {
    id: "guofeng-palette",
    name: "Guofeng Palette LoRA",
    label: "国风色彩",
    preset: "cinematic",
    default_weight: 0.6,
    description: "控制绢色、水墨纹理和东方低饱和色。",
  },
  {
    id: "healing-daylight",
    name: "Healing Daylight LoRA",
    label: "治愈柔光",
    preset: "cinematic",
    default_weight: 0.54,
    description: "控制清透柔光、暖色空气感和生活氛围。",
  },
];

const styleCatalog = [
  {
    label: "写真",
    preset: "cinematic",
    prompt: "indoor portrait photo session soft window light natural skin texture 50mm shallow depth of field lifestyle",
    promptSnippet: "室内写真，自然肤色，柔和窗光",
    image: "./assets/styles/style-realistic.png",
    imageClass: "realistic",
    summary: "室内窗光 · 真实肤质",
    styleWeight: 0.58,
    loraId: "portrait-consistency",
    loraWeight: 0.7,
    controls: [
      { id: "capture", label: "拍摄", value: "室内写真" },
      { id: "light", label: "光线", value: "窗边柔光" },
      { id: "color", label: "肤质", value: "真实细腻" },
      { id: "lens", label: "镜头", value: "50mm 半身" },
    ],
    cardParams: [
      { label: "场景", value: "室内" },
      { label: "光线", value: "窗光" },
      { label: "质感", value: "写真" },
    ],
    tokens: ["portrait-photo", "window-light", "natural-skin", "50mm", "identity-lock"],
  },
  {
    label: "摄影",
    preset: "cinematic",
    prompt: "outdoor portrait photography golden daylight alley wall natural bokeh 50mm realistic skin",
    promptSnippet: "户外摄影，日光逆光，浅景深",
    image: "./assets/styles/style-photo.png",
    imageClass: "photo",
    summary: "户外日光 · 背景虚化",
    styleWeight: 0.62,
    loraId: "soft-daylight-pro",
    loraWeight: 0.6,
    controls: [
      { id: "capture", label: "拍摄", value: "户外人像" },
      { id: "light", label: "光线", value: "日光逆光" },
      { id: "color", label: "色调", value: "清透暖调" },
      { id: "lens", label: "镜头", value: "50mm 浅景深" },
    ],
    cardParams: [
      { label: "场景", value: "户外" },
      { label: "光线", value: "日光" },
      { label: "景深", value: "浅" },
    ],
    tokens: ["outdoor-photo", "backlight", "natural-bokeh", "warm-skin", "portrait"],
  },
  {
    label: "商业广告",
    preset: "commercial",
    prompt: "luxury skincare product advertising golden serum bottle glass reflection macro studio light premium brand campaign",
    promptSnippet: "商业广告，金色产品棚拍，玻璃反射高光",
    image: "./assets/styles/style-commercial-ad.png",
    imageClass: "commercial-ad",
    summary: "产品棚拍 · 金色高光",
    styleWeight: 0.68,
    loraId: "brand-campaign",
    loraWeight: 0.66,
    controls: [
      { id: "subject", label: "主体", value: "护肤精华瓶" },
      { id: "light", label: "光线", value: "金色棚拍高光" },
      { id: "material", label: "材质", value: "玻璃与液体反射" },
      { id: "composition", label: "构图", value: "产品居中近景" },
    ],
    cardParams: [
      { label: "主体", value: "产品" },
      { label: "光线", value: "金光" },
      { label: "质感", value: "奢华" },
    ],
    tokens: ["luxury-product", "golden-light", "glass-reflection", "premium-skincare", "brand-campaign"],
  },
  {
    label: "商业海报",
    preset: "commercial",
    prompt: "premium product poster hero serum bottle golden cosmetic campaign flowers floating spheres centered composition glossy reflection",
    promptSnippet: "商业海报，中心产品主视觉，花瓣金球高光",
    image: "./assets/styles/style-commercial-poster.png",
    imageClass: "commercial-poster",
    summary: "主视觉海报 · 中心产品",
    styleWeight: 0.72,
    loraId: "campaign-poster",
    loraWeight: 0.64,
    controls: [
      { id: "layout", label: "版式", value: "海报主视觉" },
      { id: "subject", label: "主体", value: "中心产品瓶" },
      { id: "props", label: "元素", value: "花瓣与金色球体" },
      { id: "finish", label: "质感", value: "高端广告精修" },
    ],
    cardParams: [
      { label: "构图", value: "居中" },
      { label: "元素", value: "花球" },
      { label: "质感", value: "海报" },
    ],
    tokens: ["product-poster", "hero-packshot", "golden-campaign", "glossy-reflection", "premium-layout"],
  },
  {
    label: "动漫",
    preset: "anime",
    prompt: "anime character portrait clean line art warm window light soft cel shading delicate eyes",
    promptSnippet: "动漫角色，清晰线稿，暖色窗光",
    image: "./assets/styles/style-anime.png",
    imageClass: "anime",
    summary: "清晰线稿 · 暖色日系",
    styleWeight: 0.68,
    loraId: "anime-clean-line",
    loraWeight: 0.64,
    controls: [
      { id: "linework", label: "线稿", value: "清晰闭合线" },
      { id: "shading", label: "上色", value: "柔和赛璐璐" },
      { id: "highlight", label: "高光", value: "窗边暖光" },
      { id: "composition", label: "构图", value: "半身近景" },
    ],
    cardParams: [
      { label: "线稿", value: "清晰" },
      { label: "上色", value: "赛璐璐" },
      { label: "光感", value: "暖" },
    ],
    tokens: ["anime-face", "clean-line", "cel-shading", "warm-window-light"],
  },
  {
    label: "插画",
    preset: "cinematic",
    prompt: "soft digital illustration painterly brush texture airy window light pastel portrait editorial composition",
    promptSnippet: "柔光插画，绘画笔触，浅色空气感",
    image: "./assets/styles/style-illustration.png",
    imageClass: "illustration",
    summary: "绘画笔触 · 柔光空气感",
    styleWeight: 0.7,
    loraId: "editorial-illustration",
    loraWeight: 0.6,
    controls: [
      { id: "brush", label: "笔触", value: "柔和刷痕" },
      { id: "paper", label: "质感", value: "轻纸感纹理" },
      { id: "palette", label: "配色", value: "浅暖低饱和" },
      { id: "composition", label: "构图", value: "窗边人物" },
    ],
    cardParams: [
      { label: "笔触", value: "手绘" },
      { label: "光线", value: "柔光" },
      { label: "配色", value: "浅暖" },
    ],
    tokens: ["illustrated", "painterly", "soft-texture", "pastel-air"],
  },
  {
    label: "3D",
    preset: "cinematic",
    prompt: "cinematic 3d character render subsurface skin glossy hair volumetric window light realistic material",
    promptSnippet: "3D 角色渲染，材质高光，窗边体积光",
    image: "./assets/styles/style-render3d.png",
    imageClass: "render3d",
    summary: "材质高光 · 立体角色",
    styleWeight: 0.72,
    loraId: "render-3d-polish",
    loraWeight: 0.58,
    controls: [
      { id: "material", label: "材质", value: "次表面皮肤" },
      { id: "lighting", label: "灯光", value: "窗边体积光" },
      { id: "render", label: "渲染", value: "高光抛光面" },
      { id: "camera", label: "镜头", value: "角色近景" },
    ],
    cardParams: [
      { label: "材质", value: "高光" },
      { label: "光线", value: "体积" },
      { label: "渲染", value: "3D" },
    ],
    tokens: ["3d-render", "subsurface", "glossy-hair", "volumetric-light"],
  },
  {
    label: "美剧",
    preset: "commercial",
    prompt: "american tv drama still moody practical lighting warm interior cinematic color grade shallow depth",
    promptSnippet: "美剧剧照，室内低照度，叙事布光",
    image: "./assets/styles/style-drama.png",
    imageClass: "drama",
    summary: "室内低照 · 叙事剧照",
    styleWeight: 0.66,
    loraId: "drama-still",
    loraWeight: 0.62,
    controls: [
      { id: "scene", label: "场面", value: "剧照式叙事" },
      { id: "light", label: "布光", value: "室内实景灯" },
      { id: "grade", label: "色调", value: "低饱和暖灰" },
      { id: "camera", label: "镜头", value: "剧集近中景" },
    ],
    cardParams: [
      { label: "布光", value: "低照" },
      { label: "色调", value: "暖灰" },
      { label: "镜头", value: "剧照" },
    ],
    tokens: ["drama-still", "practical-light", "moody", "cinematic-grade"],
  },
  {
    label: "国风",
    preset: "cinematic",
    prompt: "chinese guofeng portrait hanfu garden blossoms silk fan soft backlight elegant classical composition",
    promptSnippet: "国风汉服，园林花影，团扇柔光",
    image: "./assets/styles/style-guofeng.png",
    imageClass: "guofeng",
    summary: "汉服园林 · 团扇花影",
    styleWeight: 0.64,
    loraId: "guofeng-palette",
    loraWeight: 0.62,
    controls: [
      { id: "styling", label: "造型", value: "汉服发饰" },
      { id: "light", label: "光线", value: "庭院柔逆光" },
      { id: "palette", label: "色彩", value: "玉白暖金" },
      { id: "composition", label: "道具", value: "团扇花枝" },
    ],
    cardParams: [
      { label: "造型", value: "汉服" },
      { label: "道具", value: "团扇" },
      { label: "场景", value: "园林" },
    ],
    tokens: ["guofeng", "hanfu", "silk-fan", "blossoms", "soft-backlight"],
  },
  {
    label: "治愈",
    preset: "cinematic",
    prompt: "healing anime lifestyle sunny room open window greenery reading book cat warm pastel daylight peaceful mood",
    promptSnippet: "治愈日常，阳光房间，阅读和猫",
    image: "./assets/styles/style-healing.png",
    imageClass: "healing",
    summary: "阳光房间 · 阅读陪伴",
    styleWeight: 0.61,
    loraId: "healing-daylight",
    loraWeight: 0.56,
    controls: [
      { id: "mood", label: "氛围", value: "安静陪伴感" },
      { id: "light", label: "光线", value: "午后暖阳" },
      { id: "palette", label: "色彩", value: "浅绿奶油色" },
      { id: "composition", label: "元素", value: "书本与猫" },
    ],
    cardParams: [
      { label: "氛围", value: "治愈" },
      { label: "光线", value: "暖阳" },
      { label: "元素", value: "书猫" },
    ],
    tokens: ["healing", "sunny-room", "reading", "cat", "warm-pastel"],
  },
];

const styleLabelAliases = new Map([
  ["写实", "写真"],
  ["真实", "写真"],
  ["真人", "写真"],
  ["3D 渲染", "3D"],
  ["3D渲染", "3D"],
  ["美剧质感", "美剧"],
  ["剧照", "美剧"],
  ["商业", "商业广告"],
  ["广告", "商业广告"],
  ["商广", "商业广告"],
  ["海报", "商业海报"],
  ["商业大片", "商业海报"],
]);

function canonicalStyleLabel(label) {
  return styleLabelAliases.get(label) || label;
}

const fallbackGenerations = [1, 2, 3, 4].map((variant) => ({
  id: `local-${variant}`,
  character_id: "lina",
  character_name: "Lina",
  character_version: 1,
  prompt: "清晨咖啡馆",
  state: "calm",
  size: "3:4",
  image: `assets/persona-ref-${variant}.png`,
  favorite: variant === 1,
  variant,
  drift_risk: "low",
  identity_weight: 0.8,
  style_weight: 0.6,
  lora_id: "portrait-consistency",
  lora_name: "人像一致性",
  lora_weight: 0.72,
  quality: {
    face_match_score: 0.92,
    threshold: 0.82,
    match: true,
    status: "pass",
    identity_margin: 0.2,
    review_note: "身份权重高于风格，生成结果通过本地一致性质检。",
  },
}));

const fallbackProjects = [
  {
    id: "light-portrait-playground",
    name: "轻写真试玩",
    user_segment: "普通用户",
    level: "Level 1 Image Tool",
    character_ids: ["lina"],
    goal: "上传参考脸并快速生成一组写真",
    channels: ["头像", "朋友圈"],
    deliverables: ["1:1 头像", "3:4 写真", "收藏精选"],
    status: "draft",
    counts: { characters: 1, generations: 4, favorites: 1, deliverables: 3 },
    recommendations: ["上传 3 张以上清晰人脸", "使用轻写真模板", "收藏最稳定的一组图"],
  },
  {
    id: "creator-character-series",
    name: "创作者角色系列",
    user_segment: "创作者",
    level: "Level 3 Character OS",
    character_ids: ["lina", "kira"],
    goal: "围绕同一角色持续产出小红书 / 抖音系列图",
    channels: ["小红书", "抖音", "短剧分镜"],
    deliverables: ["角色版本", "系列封面", "场景记忆", "风格预设"],
    status: "active",
    counts: { characters: 2, generations: 4, favorites: 1, deliverables: 4 },
    recommendations: ["按系列场景生成", "复用高分角度", "沉淀版本历史和失败风格"],
  },
  {
    id: "brand-virtual-ip",
    name: "品牌虚拟模特 IP",
    user_segment: "商业用户",
    level: "Level 4 Visual IP System",
    character_ids: ["alex"],
    goal: "沉淀长期可复用的品牌广告模特资产",
    channels: ["广告投放", "电商主图", "品牌海报"],
    deliverables: ["IP 资产包", "商业授权摘要", "品牌 LoRA", "版本审阅记录"],
    status: "in_review",
    counts: { characters: 1, generations: 0, favorites: 0, deliverables: 4 },
    recommendations: ["身份权重保持 0.90+", "绑定品牌 LoRA", "导出 IP 资产包并进入审阅"],
  },
];

const imageModelPresets = [
  {
    provider: "fal",
    label: "fal.ai",
    display: "fal.ai · FLUX 1.1 Pro Ultra",
    model: "fal-ai/flux-pro/v1.1-ultra",
    baseUrl: "https://fal.run",
  },
  {
    provider: "fal",
    label: "fal.ai",
    display: "fal.ai · FLUX.1 Kontext Max",
    model: "fal-ai/flux-pro/kontext/max",
    baseUrl: "https://fal.run",
  },
  {
    provider: "fal",
    label: "fal.ai",
    display: "fal.ai · FLUX.1 Pro Fill",
    model: "fal-ai/flux-pro/v1/fill",
    baseUrl: "https://fal.run",
  },
  {
    provider: "fal",
    label: "fal.ai",
    display: "fal.ai · FLUX.1 Pro Erase",
    model: "fal-ai/flux-pro/v1/erase",
    baseUrl: "https://fal.run",
  },
  {
    provider: "flux",
    label: "FLUX",
    display: "FLUX · FLUX.2 Max",
    model: "flux-2-max",
    baseUrl: "https://api.bfl.ai/v1",
  },
  {
    provider: "stable-diffusion",
    label: "Stable Diffusion",
    display: "Stable Diffusion · Stable Image Ultra",
    model: "stable-image-ultra",
    baseUrl: "https://api.stability.ai",
  },
  {
    provider: "midjourney",
    label: "Midjourney",
    display: "Midjourney · V8.1",
    model: "midjourney-v8.1",
    baseUrl: "",
  },
  {
    provider: "openai",
    label: "OpenAI",
    display: "OpenAI · GPT-Image-1.5",
    model: "gpt-image-1.5",
    baseUrl: "https://api.openai.com/v1",
  },
  {
    provider: "google-imagen",
    label: "Google Imagen",
    display: "Google Imagen · Nano Banana 2",
    model: "gemini-3.1-flash-image",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta",
  },
  {
    provider: "wanx",
    label: "通义万象",
    display: "通义万象 · Wan2.6 Image",
    model: "wan2.6-image",
    baseUrl: "https://dashscope.aliyuncs.com/api/v1",
  },
  {
    provider: "zhipu",
    label: "智谱 AI",
    display: "智谱 AI · GLM-Image",
    model: "glm-image",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
  },
  {
    provider: "volcengine",
    label: "火山引擎",
    display: "火山引擎 · Seedream 5.0",
    model: "doubao-seedream-5-0-260128",
    baseUrl: "https://ark.cn-beijing.volces.com/api/v3",
  },
  {
    provider: "kling",
    label: "可灵 AI",
    display: "可灵 AI · Kling v3",
    model: "kling-v3",
    baseUrl: "https://api-singapore.klingai.com",
  },
  {
    provider: "wenxin",
    label: "文心一格",
    display: "文心一格 · 精调模型",
    model: "wenxin-yige-sft",
    baseUrl: "",
  },
  {
    provider: "custom",
    label: "自定义",
    display: "自定义 API",
    model: "",
    baseUrl: "",
  },
];

const referenceCategories = {
  face: {
    label: "人脸",
    hint: "人脸一致性参考",
    uploadLabel: "上传人脸",
    items: [
      {
        id: "face-main",
        label: "主图",
        image: "./assets/persona-ref-1.png",
        alt: "Reference face selected",
        prompt: "保持参考人脸五官比例和脸型",
        active: true,
      },
      {
        id: "face-side",
        label: "侧脸",
        image: "./assets/persona-ref-2.png",
        alt: "Reference face side angle",
        prompt: "参考侧脸角度，保持同一角色身份",
      },
      {
        id: "face-turn",
        label: "回眸",
        image: "./assets/persona-ref-3.png",
        alt: "Reference face turn back",
        prompt: "参考回眸姿态，保持脸部结构稳定",
      },
      {
        id: "face-smile",
        label: "微笑",
        image: "./assets/persona-ref-4.png",
        alt: "Reference face smile",
        prompt: "参考自然微笑和面部表情",
      },
    ],
  },
  outfit: {
    label: "服装",
    hint: "衣服、裙子、材质参考",
    uploadLabel: "上传服装",
    items: [
      {
        id: "outfit-white-blouse",
        label: "白色上衣",
        visual: "white-blouse",
        prompt: "参考服装：白色轻薄上衣，干净自然，布料有柔和褶皱",
      },
      {
        id: "outfit-satin-dress",
        label: "缎面裙",
        visual: "satin-dress",
        prompt: "参考服装：浅色缎面连衣裙，垂坠感明显，适合写真",
      },
      {
        id: "outfit-knit-cardigan",
        label: "针织外套",
        visual: "knit-cardigan",
        prompt: "参考服装：浅色针织外套，柔软纹理，温和生活感",
      },
    ],
  },
  accessory: {
    label: "配饰",
    hint: "包包、耳饰、丝巾参考",
    uploadLabel: "上传配饰",
    items: [
      {
        id: "accessory-leather-bag",
        label: "手提包",
        visual: "leather-bag",
        prompt: "参考配饰：小号皮质手提包，低调商业感",
      },
      {
        id: "accessory-pearl-earring",
        label: "耳饰",
        visual: "pearl-earring",
        prompt: "参考配饰：小珍珠耳饰，精致但不抢脸",
      },
      {
        id: "accessory-silk-scarf",
        label: "丝巾",
        visual: "silk-scarf",
        prompt: "参考配饰：暖色丝巾，轻微飘动，增加层次",
      },
    ],
  },
  scene: {
    label: "环境",
    hint: "场景、光线、空间参考",
    uploadLabel: "上传环境",
    items: [
      {
        id: "scene-park",
        label: "公园",
        image: "./assets/persona-ref-1.png",
        alt: "Park environment reference",
        prompt: "参考环境：清晨户外公园，自然逆光，背景绿植虚化",
      },
      {
        id: "scene-riverside",
        label: "河边",
        image: "./assets/persona-ref-3.png",
        alt: "Riverside environment reference",
        prompt: "参考环境：河边步道，冷色水面反光，浅景深",
      },
      {
        id: "scene-garden",
        label: "花园",
        image: "./assets/persona-ref-4.png",
        alt: "Garden environment reference",
        prompt: "参考环境：花园小路，暖色阳光，花丛背景",
      },
      {
        id: "scene-studio",
        label: "棚拍",
        visual: "studio",
        prompt: "参考环境：干净摄影棚，受控主光，商业头像质感",
      },
    ],
  },
};
const referenceCollectionKinds = ["outfit", "accessory", "scene"];
const defaultReferenceCollections = Object.fromEntries(
  referenceCollectionKinds.map((kind) => [
    kind,
    (referenceCategories[kind]?.items || []).map((item) => ({ ...item })),
  ]),
);

const promptInput = document.querySelector("#promptInput");
const negativePromptInput = document.querySelector("#negativePromptInput");
const promptCount = document.querySelector("#promptCount");
const negativeCount = document.querySelector("#negativeCount");
const clearPromptButton = document.querySelector("#clearPromptButton");
const clearNegativeButton = document.querySelector("#clearNegativeButton");
const characterList = document.querySelector("#characterList");
const characterName = document.querySelector("#characterName");
const consistencyScore = document.querySelector("#consistencyScore");
const versionBadge = document.querySelector("#versionBadge");
const lastUsedBadge = document.querySelector("#lastUsedBadge");
const activeCharacterThumb = document.querySelector(".active-character .row-thumb");
const stylePills = document.querySelector("#stylePills");
const loraSelect = document.querySelector("#loraSelect");
const loraRange = document.querySelector("#loraRange");
const loraValue = document.querySelector("#loraValue");
const loraBadge = document.querySelector("#loraBadge");
const detailIdentity = document.querySelector("#detailIdentity");
const detailIdentityValue = document.querySelector("#detailIdentityValue");
const memoryList = document.querySelector(".memory-list");
const memoryInsights = document.querySelector("#memoryInsights");
const identityRange = document.querySelector("#identityRange");
const identityValue = document.querySelector("#identityValue");
const identityReadiness = document.querySelector("#identityReadiness");
const styleRange = document.querySelector("#styleRange");
const styleValue = document.querySelector("#styleValue");
const stateSelect = document.querySelector("#stateSelect");
const poseControlSelect = document.querySelector("#poseControlSelect");
const modelSelect = document.querySelector("#modelSelect");
const generateButton = document.querySelector("#generateButton");
const preflightButton = document.querySelector("#preflightButton");
const createCharacterButton = document.querySelector("#createCharacterButton");
const editCharacterButton = document.querySelector("#editCharacterButton");
const trainMoreButton = document.querySelector("#trainMoreButton");
const versionHistoryButton = document.querySelector("#versionHistoryButton");
const exportProjectButton = document.querySelector("#exportProjectButton");
const upgradeButton = document.querySelector(".upgrade-button");
const accountCenterButton = document.querySelector("#accountCenterButton");
const profileApiStatus = document.querySelector("#profileApiStatus");
const accountPopover = document.querySelector("#accountPopover");
const accountPopoverBody = document.querySelector("#accountPopoverBody");
const closeAccountPopover = document.querySelector("#closeAccountPopover");
const referenceToggle = document.querySelector("#referenceToggle");
const faceEnhanceButton = document.querySelector("#faceEnhanceButton");
const preserveFeaturesButton = document.querySelector("#preserveFeaturesButton");
const stylePresetGrid = document.querySelector("#stylePresetGrid");
const moreStylesButton = document.querySelector("#moreStylesButton");
const styleInspectButton = document.querySelector("#styleInspectButton");
const styleLibraryOverlay = document.querySelector("#styleLibraryOverlay");
const styleLibraryGrid = document.querySelector("#styleLibraryGrid");
const styleLibraryDetail = document.querySelector("#styleLibraryDetail");
const closeStyleLibrary = document.querySelector("#closeStyleLibrary");
const favoritesOnly = document.querySelector("#favoritesOnly");
const sortSelect = document.querySelector("#sortSelect");
const gridViewButton = document.querySelector("#gridViewButton");
const listViewButton = document.querySelector("#listViewButton");
const outputGrid = document.querySelector("#outputGrid");
const generationNotice = document.querySelector("#generationNotice");
const workspaceModePanel = document.querySelector("#workspaceModePanel");
const modeContextPanel = document.querySelector("#modeContextPanel");
const workspaceTitle = document.querySelector(".workspace-header h1");
const referenceRail = document.querySelector(".reference-rail");
const referenceUploadInput = document.querySelector("#referenceUploadInput");
const identityStrip = document.querySelector(".identity-strip");
const referenceList = document.querySelector(".reference-list");
const referenceKindTabs = document.querySelector("#referenceKindTabs");
const referenceRailHint = document.querySelector("#referenceRailHint");
const advancedToggle = document.querySelector("#advancedToggle");
const advancedPanel = document.querySelector("#advancedPanel");
const fusionDiagnoseButton = document.querySelector("#fusionDiagnoseButton");
const fusionPanel = document.querySelector("#fusionPanel");
const costLine = document.querySelector(".cost-line");
const creditPill = document.querySelector(".credit-pill");
const apiStatus = document.querySelector("#apiStatus");
const appShell = document.querySelector(".app-shell");
const navItems = document.querySelectorAll(".nav-item");
const modeTabs = document.querySelectorAll(".tab");
const imageDetailOverlay = document.querySelector("#imageDetailOverlay");
const detailImage = document.querySelector("#detailImage");
const detailMeta = document.querySelector("#detailMeta");
const detailPrompt = document.querySelector("#detailPrompt");
const detailNegativePrompt = document.querySelector("#detailNegativePrompt");
const detailConsistency = document.querySelector("#detailConsistency");
const detailQuality = document.querySelector("#detailQuality");
const detailModelRoute = document.querySelector("#detailModelRoute");
const detailJob = document.querySelector("#detailJob");
const detailReferenceGuidance = document.querySelector("#detailReferenceGuidance");
const detailConditioning = document.querySelector("#detailConditioning");
const detailLora = document.querySelector("#detailLora");
const closeImageDetail = document.querySelector("#closeImageDetail");
const detailDownloadButton = document.querySelector("#detailDownloadButton");
const detailFavoriteButton = document.querySelector("#detailFavoriteButton");
const detailReuseButton = document.querySelector("#detailReuseButton");
const detailLockButton = document.querySelector("#detailLockButton");
const detailCanvasEditButton = document.querySelector("#detailCanvasEditButton");
const detailRemixButton = document.querySelector("#detailRemixButton");
const detailDeleteButton = document.querySelector("#detailDeleteButton");
const canvasEditPanel = document.querySelector("#canvasEditPanel");
const canvasEditCanvas = document.querySelector("#canvasEditCanvas");
const canvasEditHint = document.querySelector("#canvasEditHint");
const canvasClearButton = document.querySelector("#canvasClearButton");
const canvasSubmitEditButton = document.querySelector("#canvasSubmitEditButton");
const canvasEditInstruction = document.querySelector("#canvasEditInstruction");

const fallbackAccountPlans = [
  { id: "free", label: "免费版", credits: 1200, monthly_credits: 1200, badge: "Free", user_segment: "普通用户", cost_per_image: 2, features: ["轻量写真", "基础角色资产", "本地项目导出"] },
  { id: "upgrade-creator", label: "创作者 Pro", credits: 2000, monthly_credits: 2000, badge: "Pro", user_segment: "创作者", cost_per_image: 2, features: ["角色版本历史", "批量生成", "记忆资产管理"] },
  { id: "upgrade-business", label: "商业团队", credits: 8000, monthly_credits: 8000, badge: "Team", user_segment: "商业用户", cost_per_image: 2, features: ["共享角色资产", "品牌 LoRA", "IP 资产包导出"] },
];
const demoPlans = Object.fromEntries(fallbackAccountPlans.filter((plan) => plan.id !== "free").map((plan) => [plan.id, plan]));
const subscriptionKey = "persona-studio-demo-plan";
const modelSelectStorageKey = "persona-studio:last-image-model";

let characters = fallbackCharacters;
let generations = fallbackGenerations;
let loras = fallbackLoras;
let projects = fallbackProjects;
let generationJobs = [];
let assetLibrary = { summary: {}, filters: { types: [] }, items: [] };
let systemReadiness = null;
let assetLibraryQuery = "";
let assetLibraryType = "all";
let activeCharacterId = "lina";
let activeGenerationMode = "文生图";
let activeProjectId = "creator-character-series";
let activePlanId = window.localStorage.getItem(subscriptionKey) || "free";
let accountPlans = fallbackAccountPlans;
let accountState = normalizeAccountState({ plan_id: activePlanId });
let apiAvailable = false;
let apiSettings = { api: { enabled: false, provider: "openai", base_url: "", model: "", api_key_set: false, access_key_set: false, secret_key_set: false, auth_configured: false, profiles: {} } };
let providerStatus = { summary: {}, providers: [] };
let draggedReferenceCard = null;
let draggedReferenceOriginalIndex = -1;
let selectedGenerationId = "";
let versionSnapshots = [];
let pendingDeleteConfirmation = null;
let activeReferenceKind = "face";
let pendingReferenceUploadKind = "face";
let pendingReferenceReplaceTarget = null;
let latestGenerationIds = new Set();
let activeMemoryEntries = [];
let activeStyleLibraryLabel = "写真";
let styleLibraryProfiles = {};
let canvasEditState = {
  open: false,
  drawing: false,
  generationId: "",
  strokes: [],
  activeStroke: null,
};

renderLoraSelect();
updatePromptCounters();
updateGenerateSummary();
applySubscriptionState();
renderReferenceRail();
initializeReferenceOrdering();
loadLoras();
loadCharacters();

promptInput.addEventListener("input", () => {
  updatePromptCounters();
});

negativePromptInput.addEventListener("input", () => {
  updatePromptCounters();
});

detailIdentity.addEventListener("input", () => {
  syncIdentity(detailIdentity.value);
});

identityRange.addEventListener("input", () => {
  syncIdentity(identityRange.value);
});

styleRange.addEventListener("input", () => {
  syncStyle(styleRange.value);
});

loraRange.addEventListener("input", () => {
  syncLoraWeight(loraRange.value);
});

loraSelect.addEventListener("change", () => {
  applyLoraSelection(loraSelect.value, true);
});

modelSelect.addEventListener("change", () => {
  persistSelectedImageModel();
  apiStatus.textContent = `模型已切换：${selectedImageModelLabel()}`;
});

poseControlSelect.addEventListener("change", () => {
  apiStatus.textContent = `姿态锁：${poseControlLabel(poseControlSelect.value)}`;
});

document.querySelectorAll('input[name="count"]').forEach((input) => {
  input.addEventListener("change", () => {
    updateGenerateSummary();
  });
});

document.querySelectorAll('input[name="size"]').forEach((input) => {
  input.addEventListener("change", () => {
    apiStatus.textContent = `尺寸已切换为 ${getCheckedValue("size")}`;
  });
});

generateButton.addEventListener("click", () => {
  generateConditioning();
});

preflightButton.addEventListener("click", () => {
  runGenerationPreflight();
});

createCharacterButton.addEventListener("click", () => {
  createCharacter();
});

editCharacterButton.addEventListener("click", () => {
  showCharacterEditor();
});

trainMoreButton.addEventListener("click", () => {
  trainMore();
});

versionHistoryButton.addEventListener("click", () => {
  showVersions();
});

exportProjectButton.addEventListener("click", () => {
  exportProject();
});

upgradeButton.addEventListener("click", () => {
  setActiveNavByName("模型广场");
  setWorkspaceMode("模型广场", { showPlans: true });
});

accountCenterButton.addEventListener("click", () => {
  openAccountCenter();
});

closeAccountPopover.addEventListener("click", () => {
  hideAccountCenter();
});

favoritesOnly.addEventListener("change", () => {
  renderGenerationGrid();
});

sortSelect.addEventListener("change", () => {
  renderGenerationGrid();
  apiStatus.textContent = `结果排序：${sortSelect.value}`;
});

gridViewButton.addEventListener("click", () => {
  setResultView("grid");
});

listViewButton.addEventListener("click", () => {
  setResultView("list");
});

advancedToggle.addEventListener("click", () => {
  const willOpen = advancedPanel.hidden;
  advancedPanel.hidden = !willOpen;
  advancedToggle.setAttribute("aria-expanded", String(willOpen));
  apiStatus.textContent = willOpen ? "高级参数已展开" : "高级参数已收起";
});

fusionDiagnoseButton.addEventListener("click", () => {
  diagnoseFusionConditioning();
});

navItems.forEach((button) => {
  button.addEventListener("click", () => {
    hideAccountCenter();
    setActiveButton(navItems, button);
    setWorkspaceMode(button.dataset.nav);
  });
});

modeTabs.forEach((button) => {
  button.addEventListener("click", () => {
    setActiveButton(modeTabs, button);
    setGenerationMode(button.dataset.mode);
  });
});

clearPromptButton.addEventListener("click", () => {
  promptInput.value = "";
  updatePromptCounters();
  promptInput.focus();
  apiStatus.textContent = "提示词已清空";
});

clearNegativeButton.addEventListener("click", () => {
  negativePromptInput.value = "";
  updatePromptCounters();
  negativePromptInput.focus();
  apiStatus.textContent = "反向提示词已清空";
});

document.querySelector("#randomPrompt").addEventListener("click", () => {
  promptInput.value = "雨夜街道，角色回头看向镜头，湿润反光路面，电影感蓝绿色调，身份锁定加强，三分之二侧脸";
  negativePromptInput.value = "模糊，低质量，脸部漂移，多余手指，过曝，强噪点，五官错位";
  updatePromptCounters();
  apiStatus.textContent = "已填入随机提示词";
});

document.querySelector("#optimizePrompt").addEventListener("click", () => {
  if (!promptInput.value.includes("身份锁定")) {
    promptInput.value = `${promptInput.value}，身份锁定，高一致性面部结构`;
  }
  if (!negativePromptInput.value.includes("脸部漂移")) {
    negativePromptInput.value = `${negativePromptInput.value}，脸部漂移`;
  }
  updatePromptCounters();
  apiStatus.textContent = "已优化提示词与反向提示词";
});

referenceToggle.addEventListener("click", () => {
  const enabled = referenceToggle.getAttribute("aria-pressed") !== "true";
  referenceToggle.setAttribute("aria-pressed", String(enabled));
  referenceToggle.classList.toggle("is-on", enabled);
  document.querySelector(".face-card")?.classList.toggle("is-disabled", !enabled);
  apiStatus.textContent = enabled ? "人脸参考已启用" : "人脸参考已关闭";
});

faceEnhanceButton.addEventListener("click", () => {
  const nextValue = Math.min(0.95, Number(identityRange.value) + 0.04);
  syncIdentity(nextValue);
  apiStatus.textContent = `人脸增强已开启 · 相似度 ${Number(nextValue).toFixed(2)}`;
});

preserveFeaturesButton.addEventListener("click", () => {
  const nextValue = Math.max(0.86, Number(identityRange.value));
  syncIdentity(nextValue);
  if (!negativePromptInput.value.includes("五官错位")) {
    negativePromptInput.value = `${negativePromptInput.value}，五官错位`;
  }
  updatePromptCounters();
  apiStatus.textContent = "已提高五官保持约束";
});

stylePresetGrid.addEventListener("click", (event) => {
  const button = event.target.closest(".style-swatch");
  if (!button) return;
  setActiveButton(stylePresetGrid.querySelectorAll(".style-swatch"), button);
  applyStylePreset(button.dataset.style);
});

moreStylesButton.addEventListener("click", () => {
  openStyleLibrary();
});

styleInspectButton.addEventListener("click", () => {
  showStyleAssetPanel();
});

identityStrip.addEventListener("click", (event) => {
  handleReferenceClick(event);
});

referenceKindTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-reference-kind]");
  if (!button) return;
  setReferenceKind(button.dataset.referenceKind);
});

referenceList.addEventListener("click", (event) => {
  handleReferenceClick(event);
});

referenceUploadInput.addEventListener("change", () => {
  uploadReferenceFiles(referenceUploadInput.files);
});

workspaceModePanel.addEventListener("click", handlePanelClick);
workspaceModePanel.addEventListener("input", (event) => {
  const searchInput = event.target.closest("#assetLibrarySearch");
  if (!searchInput) return;
  assetLibraryQuery = searchInput.value;
  renderAssetLibraryRows();
});
workspaceModePanel.addEventListener("change", (event) => {
  const typeSelect = event.target.closest("#assetLibraryType");
  if (!typeSelect) return;
  assetLibraryType = typeSelect.value || "all";
  renderAssetLibraryRows();
});
workspaceModePanel.addEventListener("submit", (event) => {
  if (event.target.matches("#apiSettingsForm")) {
    event.preventDefault();
    saveApiSettings();
    return;
  }
  if (event.target.matches("#characterEditForm")) {
    event.preventDefault();
    saveCharacterProfile();
  }
});
accountPopover.addEventListener("click", handlePanelClick);
accountPopover.addEventListener("submit", (event) => {
  if (!event.target.matches("#apiSettingsForm")) return;
  event.preventDefault();
  saveApiSettings();
});
modeContextPanel.addEventListener("click", handlePanelClick);

memoryInsights.addEventListener("click", async (event) => {
  const manageButton = event.target.closest("[data-memory-action='manage']");
  if (manageButton) {
    await showMemoryStorePanel(activeCharacterId);
    return;
  }

  const button = event.target.closest("[data-memory-prompt], [data-memory-style]");
  if (!button) return;
  if (button.dataset.memoryPrompt) {
    addPromptClause(button.dataset.memoryPrompt);
    apiStatus.textContent = "已应用记忆推荐角度";
  }
  if (button.dataset.memoryStyle) {
    addPromptClause(`${button.dataset.memoryStyle} 风格，保持身份一致`);
    apiStatus.textContent = "已应用角色偏好风格";
  }
});

closeImageDetail.addEventListener("click", () => {
  closeGenerationDetail();
});

imageDetailOverlay.addEventListener("click", (event) => {
  if (event.target === imageDetailOverlay) {
    closeGenerationDetail();
  }
});

detailImage.addEventListener("load", () => {
  if (canvasEditState.open) {
    renderCanvasEdit();
  }
});

closeStyleLibrary.addEventListener("click", () => {
  closeStyleLibraryDialog();
});

styleLibraryOverlay.addEventListener("click", (event) => {
  if (event.target === styleLibraryOverlay) {
    closeStyleLibraryDialog();
    return;
  }
  const detailButton = event.target.closest("[data-style-detail]");
  if (detailButton) {
    selectStyleLibraryItem(detailButton.dataset.styleDetail);
    return;
  }
  const applyButton = event.target.closest("[data-style-apply]");
  if (applyButton) {
    applyStylePreset(applyButton.dataset.styleApply);
    renderStyleLibrary();
    renderStyleLibraryDetail(applyButton.dataset.styleApply);
    closeStyleLibraryDialog();
  }
});

detailDownloadButton.addEventListener("click", () => {
  const generation = currentDetailGeneration();
  if (!generation) return;
  downloadGeneration(generation);
});

detailFavoriteButton.addEventListener("click", async () => {
  const generation = currentDetailGeneration();
  if (!generation) return;
  const updated = await toggleFavorite(generation.id);
  if (!updated) return;
  syncDetailActionState(updated);
  apiStatus.textContent = updated.favorite ? "已收藏详情图" : "已取消收藏详情图";
});

detailReuseButton.addEventListener("click", () => {
  const generation = currentDetailGeneration();
  if (!generation) return;
  promptInput.value = generation.prompt || promptInput.value;
  negativePromptInput.value = generation.negative_prompt || negativePromptInput.value;
  updatePromptCounters();
  apiStatus.textContent = "已从详情复用提示词";
});

detailLockButton.addEventListener("click", () => {
  const nextValue = Math.min(0.95, Number(identityRange.value) + 0.05);
  syncIdentity(nextValue);
  detailConsistency.textContent = `身份 ${Number(nextValue).toFixed(2)} · 风格 ${Number(styleRange.value).toFixed(2)} · 后验匹配 ${posteriorFaceScore({ identity_weight: nextValue, style_weight: Number(styleRange.value) })}%`;
  apiStatus.textContent = `详情锁脸已加强到 ${Number(nextValue).toFixed(2)}`;
});

detailCanvasEditButton.addEventListener("click", () => {
  openCanvasEditPanel();
});

canvasClearButton.addEventListener("click", () => {
  canvasEditState.strokes = [];
  canvasEditState.activeStroke = null;
  renderCanvasEdit();
  canvasEditHint.textContent = "标记已清除，可重新涂抹要修改的区域";
});

canvasSubmitEditButton.addEventListener("click", () => {
  submitCanvasEdit();
});

canvasEditCanvas.addEventListener("pointerdown", (event) => {
  if (!canvasEditState.open) return;
  event.preventDefault();
  canvasEditCanvas.setPointerCapture(event.pointerId);
  canvasEditState.drawing = true;
  const point = canvasEditPoint(event);
  canvasEditState.activeStroke = { brush: 0.035, points: [point] };
  canvasEditState.strokes.push(canvasEditState.activeStroke);
  renderCanvasEdit();
});

canvasEditCanvas.addEventListener("pointermove", (event) => {
  if (!canvasEditState.drawing || !canvasEditState.activeStroke) return;
  event.preventDefault();
  const point = canvasEditPoint(event);
  const points = canvasEditState.activeStroke.points;
  const lastPoint = points[points.length - 1];
  if (!lastPoint || Math.hypot(point.x - lastPoint.x, point.y - lastPoint.y) > 0.004) {
    points.push(point);
    renderCanvasEdit();
  }
});

["pointerup", "pointercancel", "pointerleave"].forEach((eventName) => {
  canvasEditCanvas.addEventListener(eventName, () => {
    canvasEditState.drawing = false;
    canvasEditState.activeStroke = null;
    canvasEditHint.textContent = canvasEditState.strokes.length
      ? `${canvasEditState.strokes.length} 处标记，可继续涂抹或提交修改`
      : "在图上涂抹要修改的区域";
  });
});

detailRemixButton.addEventListener("click", () => {
  addPromptClause("生成变体，保持同一角色身份");
  syncStyle(Math.min(0.85, Number(styleRange.value) + 0.04));
  apiStatus.textContent = "已从详情准备变体参数";
});

detailDeleteButton.addEventListener("click", async () => {
  const generation = currentDetailGeneration();
  if (!generation) return;
  await confirmBeforeDelete({
    key: `generation-detail:${generation.id}`,
    button: detailDeleteButton,
    idleText: "删除",
    idleLabel: `删除生成图 ${generation.id}`,
    confirmLabel: `确认删除生成图 ${generation.id}`,
    statusText: `再次点击确认删除生成图：${generation.id}`,
    onConfirm: async () => {
      await deleteGeneration(generation.id);
      if (!generations.some((item) => item.id === generation.id)) {
        closeGenerationDetail();
      }
    },
  });
});

function currentDetailGeneration() {
  return generations.find((item) => item.id === selectedGenerationId);
}

function openCanvasEditPanel() {
  const generation = currentDetailGeneration();
  if (!generation) return;
  canvasEditState = {
    open: true,
    drawing: false,
    generationId: generation.id,
    strokes: [],
    activeStroke: null,
  };
  canvasEditPanel.hidden = false;
  canvasEditInstruction.value = "";
  canvasEditHint.textContent = "在图上涂抹要修改的区域";
  detailCanvasEditButton.setAttribute("aria-pressed", "true");
  renderCanvasEdit();
  canvasEditInstruction.focus();
  apiStatus.textContent = "已打开画布修改";
}

function closeCanvasEditPanel() {
  canvasEditState.open = false;
  canvasEditState.drawing = false;
  canvasEditState.activeStroke = null;
  canvasEditPanel.hidden = true;
  detailCanvasEditButton.setAttribute("aria-pressed", "false");
}

function canvasEditPoint(event) {
  const rect = canvasEditCanvas.getBoundingClientRect();
  const x = rect.width ? (event.clientX - rect.left) / rect.width : 0;
  const y = rect.height ? (event.clientY - rect.top) / rect.height : 0;
  return {
    x: Number(Math.max(0, Math.min(1, x)).toFixed(4)),
    y: Number(Math.max(0, Math.min(1, y)).toFixed(4)),
  };
}

function resizeCanvasEditToImage(generation) {
  const mediaFrame = detailImage.closest(".image-detail-media");
  const frameWidth = Math.max(280, Math.min(520, mediaFrame?.clientWidth || 420));
  const ratio = ratioNumberForSize(generation?.size || "3:4");
  const width = Math.round(frameWidth);
  const height = Math.round(width / ratio);
  canvasEditCanvas.width = width;
  canvasEditCanvas.height = height;
}

function renderCanvasEdit() {
  const generation = currentDetailGeneration();
  if (!generation || !canvasEditCanvas) return;
  resizeCanvasEditToImage(generation);
  const context = canvasEditCanvas.getContext("2d");
  const { width, height } = canvasEditCanvas;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#0a0d12";
  context.fillRect(0, 0, width, height);
  if (detailImage.complete && detailImage.naturalWidth) {
    const imageRatio = detailImage.naturalWidth / detailImage.naturalHeight;
    const canvasRatio = width / height;
    let drawWidth = width;
    let drawHeight = height;
    let drawX = 0;
    let drawY = 0;
    if (imageRatio > canvasRatio) {
      drawHeight = width / imageRatio;
      drawY = (height - drawHeight) / 2;
    } else {
      drawWidth = height * imageRatio;
      drawX = (width - drawWidth) / 2;
    }
    context.drawImage(detailImage, drawX, drawY, drawWidth, drawHeight);
  }
  context.fillStyle = "rgba(255, 77, 109, 0.16)";
  context.fillRect(0, 0, width, height);
  for (const stroke of canvasEditState.strokes) {
    const points = stroke.points || [];
    if (!points.length) continue;
    context.beginPath();
    context.lineCap = "round";
    context.lineJoin = "round";
    context.lineWidth = Math.max(14, Math.round(width * Number(stroke.brush || 0.035)));
    context.strokeStyle = "rgba(255, 82, 121, 0.82)";
    points.forEach((point, index) => {
      const x = point.x * width;
      const y = point.y * height;
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });
    context.stroke();
  }
}

function canvasEditMaskPayload() {
  return {
    version: 1,
    canvas_width: canvasEditCanvas.width,
    canvas_height: canvasEditCanvas.height,
    strokes: canvasEditState.strokes
      .filter((stroke) => (stroke.points || []).length)
      .map((stroke) => ({
        brush: Number(stroke.brush || 0.035),
        points: (stroke.points || []).map((point) => ({ x: point.x, y: point.y })),
      })),
  };
}

async function submitCanvasEdit() {
  const generation = currentDetailGeneration();
  const instruction = canvasEditInstruction.value.trim();
  const mask = canvasEditMaskPayload();
  if (!generation) return;
  if (!instruction) {
    canvasEditHint.textContent = "先写清楚要怎么修改";
    canvasEditInstruction.focus();
    return;
  }
  if (!mask.strokes.length) {
    canvasEditHint.textContent = "先在图上涂抹需要修改的区域";
    canvasEditCanvas.focus();
    return;
  }
  if (!apiAvailable) {
    apiStatus.textContent = "后端未连接，不能保存画布修改";
    return;
  }
  canvasSubmitEditButton.disabled = true;
  canvasSubmitEditButton.textContent = "提交中";
  try {
    const response = await fetch(`/api/generations/${generation.id}/edit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction, mask }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `画布修改失败：${response.status}`);
    }
    const created = payload.generations || (payload.generation ? [payload.generation] : []);
    generations = [...created, ...generations.filter((item) => !created.some((createdItem) => createdItem.id === item.id))];
    if (payload.job?.id) {
      generationJobs = [payload.job, ...generationJobs.filter((item) => item.id !== payload.job.id)];
    }
    if (payload.account) {
      setAccountState(payload.account);
    }
    latestGenerationIds = new Set(created.map((item) => item.id).filter(Boolean));
    showGenerationResultsAfterCreate();
    renderGenerationGrid();
    closeCanvasEditPanel();
    if (created[0]) {
      openGenerationDetail(created[0]);
    }
    apiStatus.textContent = `画布修改已返回修订图：${created[0]?.id || "新图"}`;
    showGenerationNotice("success", "画布修改已完成", "修订图已置顶显示，原图保留在作品历史中");
  } catch (error) {
    apiStatus.textContent = error.message;
    canvasEditHint.textContent = error.message;
  } finally {
    canvasSubmitEditButton.disabled = false;
    canvasSubmitEditButton.textContent = "提交修改";
  }
}

function syncDetailActionState(generation) {
  if (!generation || !detailFavoriteButton) return;
  detailFavoriteButton.textContent = generation.favorite ? "取消收藏" : "收藏";
  detailFavoriteButton.setAttribute("aria-pressed", generation.favorite ? "true" : "false");
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !styleLibraryOverlay.hidden) {
    closeStyleLibraryDialog();
    return;
  }
  if (event.key === "Escape" && !imageDetailOverlay.hidden) {
    closeGenerationDetail();
    return;
  }
  if (event.key === "Escape" && !accountPopover.hidden) {
    hideAccountCenter();
  }
});

async function handlePanelClick(event) {
  const memoryEntryPromptButton = event.target.closest("[data-memory-entry-id]");
  if (memoryEntryPromptButton) {
    const entry = activeMemoryEntries.find((item) => item.id === memoryEntryPromptButton.dataset.memoryEntryId);
    if (entry?.prompt) {
      addPromptClause(entry.prompt);
      apiStatus.textContent = "已复用记忆提示词";
    }
    return;
  }

  const memoryPromptButton = event.target.closest("[data-memory-prompt]");
  if (memoryPromptButton) {
    addPromptClause(memoryPromptButton.dataset.memoryPrompt);
    apiStatus.textContent = "已复用记忆提示词";
    return;
  }

  const promptButton = event.target.closest("[data-prompt]");
  if (promptButton) {
    promptInput.value = promptButton.dataset.prompt;
    updatePromptCounters();
    if (promptButton.dataset.style) {
      applyStylePreset(promptButton.dataset.style);
    }
    apiStatus.textContent = "已应用探索提示词";
    return;
  }

  const projectButton = event.target.closest("[data-project-id]");
  if (projectButton) {
    await selectProject(projectButton.dataset.projectId);
    return;
  }

  const projectDeleteButton = event.target.closest("[data-delete-project-id]");
  if (projectDeleteButton) {
    const projectId = projectDeleteButton.dataset.deleteProjectId;
    const project = projects.find((item) => item.id === projectId);
    await confirmBeforeDelete({
      key: `project:${projectId}`,
      button: projectDeleteButton,
      idleLabel: `删除项目 ${project?.name || projectId}`,
      confirmLabel: `确认删除项目 ${project?.name || projectId}`,
      statusText: `再次点击确认删除项目：${project?.name || projectId}`,
      onConfirm: () => deleteProject(projectId),
    });
    return;
  }

  const loraButton = event.target.closest("[data-use-lora]");
  if (loraButton) {
    applyLoraSelection(loraButton.dataset.useLora, true);
    return;
  }

  const apiActionButton = event.target.closest("[data-api-action]");
  if (apiActionButton) {
    if (apiActionButton.dataset.apiAction === "save") {
      await saveApiSettings();
    }
    if (apiActionButton.dataset.apiAction === "test") {
      await testApiSettings();
    }
    if (apiActionButton.dataset.apiAction === "clear-key") {
      await saveApiSettings({ clearKey: true });
    }
    return;
  }

  const restoreButton = event.target.closest("[data-version-restore]");
  if (restoreButton) {
    await restoreVersion(Number(restoreButton.dataset.versionRestore));
    return;
  }

  const versionButton = event.target.closest("[data-version-number]");
  if (versionButton) {
    selectVersionSnapshot(Number(versionButton.dataset.versionNumber));
    return;
  }

  const retryJobButton = event.target.closest("[data-retry-job-id]");
  if (retryJobButton) {
    await retryGenerationJob(retryJobButton.dataset.retryJobId);
    return;
  }

  const jobGenerationButton = event.target.closest("[data-open-generation-id]");
  if (jobGenerationButton) {
    openGenerationFromJob(jobGenerationButton.dataset.openGenerationId);
    return;
  }

  const assetOpenButton = event.target.closest("[data-asset-open]");
  if (assetOpenButton) {
    await openAssetLibraryItem(assetOpenButton.dataset.assetOpen, assetOpenButton.dataset.assetId || "");
    return;
  }

  const memoryDeleteButton = event.target.closest("[data-delete-memory-id]");
  if (memoryDeleteButton) {
    const memoryId = memoryDeleteButton.dataset.deleteMemoryId;
    await confirmBeforeDelete({
      key: `memory:${memoryId}`,
      button: memoryDeleteButton,
      idleLabel: "删除记忆",
      confirmLabel: "确认删除记忆",
      statusText: "再次点击确认删除这条记忆",
      onConfirm: () => deleteMemoryEntry(memoryId),
    });
    return;
  }

  const actionButton = event.target.closest("[data-workspace-action]");
  if (!actionButton) return;
  const action = actionButton.dataset.workspaceAction;
  if (action === "favorites") {
    workspaceTitle.textContent = "我的作品";
    showResultSurface({ keepWorkspacePanel: true, hideNotice: true });
    favoritesOnly.checked = true;
    renderGenerationGrid();
    apiStatus.textContent = "已切换到收藏作品";
  }
  if (action === "all") {
    workspaceTitle.textContent = "我的作品";
    showResultSurface({ keepWorkspacePanel: true, hideNotice: true });
    favoritesOnly.checked = false;
    renderGenerationGrid();
    apiStatus.textContent = "已显示全部作品";
  }
  if (action === "export") {
    exportProject();
  }
  if (action === "jobs") {
    await showGenerationJobs();
  }
  if (action === "asset-library") {
    await showAssetLibrary();
  }
  if (action === "system-readiness") {
    await showSystemReadiness();
  }
  if (action === "train-production-identity") {
    await trainProductionIdentity();
  }
  if (action === "train-character-lora") {
    await trainCharacterLora();
  }
  if (action === "initialize-deployment") {
    await initializeDeployment();
  }
  if (action === "build-release-package") {
    await buildReleasePackage();
  }
  if (action === "manage-memory") {
    await showMemoryStorePanel(activeCharacterId);
  }
  if (action === "style-assets") {
    await showStyleAssetPanel();
  }
  if (action === "generation-preflight") {
    await runGenerationPreflight();
  }
  if (action === "cancel-character-edit") {
    showGenerationResultsPanel();
    renderGenerationGrid();
    apiStatus.textContent = "角色资料编辑已取消";
  }
  if (action === "create-project") {
    await createProjectFromCurrent();
  }
  if (action === "bind-project-character") {
    await bindActiveCharacterToProject();
  }
  if (action === "export-ip-pack") {
    await exportIpPackage();
  }
  if (action === "submit-project-review") {
    await updateProjectReview("submit_review");
  }
  if (action === "approve-project") {
    await updateProjectReview("approve");
  }
  if (action === "withdraw-project-review") {
    await updateProjectReview("withdraw_review");
  }
  if (action === "upload-reference") {
    pendingReferenceUploadKind = activeReferenceKind;
    referenceUploadInput.click();
  }
  if (action === "strengthen-reference") {
    ensureReferenceEnabled();
    syncIdentity(Math.max(0.9, Number(identityRange.value)));
    apiStatus.textContent = "图生图参考约束已加强";
  }
  if (action === "mask-face") {
    openAdvancedPanel();
    addPromptClause("面部区域局部重绘，保持角色身份");
    addNegativeClause("背景变形");
    apiStatus.textContent = "局部重绘区域已设为面部";
  }
  if (action === "mask-background") {
    openAdvancedPanel();
    addPromptClause("背景保持不变，仅调整人物细节");
    addNegativeClause("背景错位");
    apiStatus.textContent = "局部重绘已启用背景保护";
  }
  if (action.startsWith("upgrade-")) {
    event.currentTarget.querySelectorAll("[data-workspace-action^='upgrade-']").forEach((button) => {
      button.classList.toggle("active", button === actionButton);
    });
    await activatePlan(action);
  }
}

outputGrid.addEventListener("click", async (event) => {
  const action = event.target.dataset.action;
  const tile = event.target.closest(".image-tile");
  const generationId = tile?.dataset.id;
  const generation = generations.find((item) => item.id === generationId);
  if (!action) {
    if (generation) {
      openGenerationDetail(generation);
    }
    return;
  }

  if (action === "reuse") {
    promptInput.value = generation?.prompt || "清晨光线中行走，柔和日光，50mm 人像，浅景深，身份锁定";
    updatePromptCounters();
    apiStatus.textContent = "已复用该图提示词";
  }

  if (action === "lock") {
    const nextValue = Math.min(0.95, Number(identityRange.value) + 0.05);
    syncIdentity(nextValue);
    apiStatus.textContent = `锁脸强度已提高到 ${Number(nextValue).toFixed(2)}`;
  }

  if (action === "remix") {
    const nextStyle = Math.min(0.85, Number(styleRange.value) + 0.04);
    syncStyle(nextStyle);
    apiStatus.textContent = `风格变体强度 ${Number(nextStyle).toFixed(2)}`;
  }

  if (action === "favorite" && generationId) {
    toggleFavorite(generationId);
  }

  if (action === "download" && generation) {
    downloadGeneration(generation);
  }

  if (action === "delete" && generationId) {
    await confirmBeforeDelete({
      key: `generation:${generationId}`,
      button: event.target,
      idleText: "删除",
      idleLabel: `删除生成图 ${generationId}`,
      confirmLabel: `确认删除生成图 ${generationId}`,
      statusText: `再次点击确认删除生成图：${generationId}`,
      onConfirm: () => deleteGeneration(generationId),
    });
  }
});

outputGrid.addEventListener("keydown", (event) => {
  if (!["Enter", " "].includes(event.key)) return;
  const tile = event.target.closest(".image-tile");
  if (!tile || event.target.closest("button")) return;
  event.preventDefault();
  const generation = generations.find((item) => item.id === tile.dataset.id);
  if (generation) {
    openGenerationDetail(generation);
  }
});

async function loadLoras() {
  try {
    const response = await fetch("/api/loras");
    if (!response.ok) {
      throw new Error(`API ${response.status}`);
    }
    const payload = await response.json();
    loras = payload.loras?.length ? payload.loras : fallbackLoras;
  } catch (error) {
    loras = fallbackLoras;
  }
  renderLoraSelect();
}

async function loadCharacters() {
  try {
    const response = await fetch("/api/characters");
    if (!response.ok) {
      throw new Error(`API ${response.status}`);
    }
    const payload = await response.json();
    characters = payload.characters.map(normalizeCharacter);
    apiAvailable = true;
    apiStatus.textContent = "后端已连接";
    await loadAccount();
    await loadGenerations();
    await loadProjects();
    await loadGenerationJobs();
    await loadApiSettings();
  } catch (error) {
    characters = fallbackCharacters;
    generations = fallbackGenerations;
    projects = fallbackProjects;
    generationJobs = [];
    apiAvailable = false;
    setAccountState({ plan_id: activePlanId });
    apiStatus.textContent = "本地预览模式";
    updateProfileApiStatus();
    restoreLastImageModelSelection();
  }

  renderCharacterList();
  setCharacter(activeCharacterId);
  renderGenerationGrid();
}

async function loadGenerations() {
  const response = await fetch("/api/generations");
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  const payload = await response.json();
  generations = payload.generations || [];
}

async function loadProjects() {
  const response = await fetch("/api/projects");
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  const payload = await response.json();
  projects = (payload.projects?.length ? payload.projects : fallbackProjects).map(normalizeProject);
  if (!projects.some((project) => project.id === activeProjectId)) {
    activeProjectId = projects[0]?.id || "";
  }
}

async function loadGenerationJobs() {
  if (!apiAvailable) {
    generationJobs = [];
    return;
  }
  const response = await fetch("/api/generation-jobs");
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  const payload = await response.json();
  generationJobs = Array.isArray(payload.jobs) ? payload.jobs : [];
}

async function loadApiSettings() {
  if (!apiAvailable) {
    providerStatus = { summary: {}, providers: [] };
    updateProfileApiStatus();
    restoreLastImageModelSelection();
    return;
  }
  try {
    const response = await fetch("/api/settings");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    apiSettings = payload.settings || apiSettings;
    await loadProviderStatus();
    updateProfileApiStatus();
    restoreLastImageModelSelection();
    if (!accountPopover.hidden) {
      renderApiSettingsPanel();
    }
  } catch (error) {
    profileApiStatus.textContent = "API 读取失败";
    providerStatus = { summary: {}, providers: [] };
    restoreLastImageModelSelection();
  }
}

async function loadProviderStatus() {
  if (!apiAvailable) {
    providerStatus = { summary: {}, providers: [] };
    return providerStatus;
  }
  try {
    const response = await fetch("/api/providers/status");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    providerStatus = {
      summary: payload.summary || {},
      providers: Array.isArray(payload.providers) ? payload.providers : [],
      active_provider: payload.active_provider || "",
      generated_at: payload.generated_at || "",
    };
  } catch (_error) {
    providerStatus = { summary: {}, providers: [] };
  }
  return providerStatus;
}

function persistSelectedImageModel() {
  try {
    window.localStorage.setItem(modelSelectStorageKey, modelSelect.value);
  } catch (_error) {
    // Local storage can be unavailable in private or restricted browser contexts.
  }
}

function storedImageModel() {
  try {
    return window.localStorage.getItem(modelSelectStorageKey) || "";
  } catch (_error) {
    return "";
  }
}

function setModelSelectValue(model, options = {}) {
  const value = String(model || "").trim();
  if (!value) return false;
  const option = Array.from(modelSelect.options).find((item) => item.value === value);
  if (!option) return false;
  modelSelect.value = value;
  if (options.persist) {
    persistSelectedImageModel();
  }
  if (options.announce) {
    apiStatus.textContent = `模型已切换：${selectedImageModelLabel()}`;
  }
  return true;
}

function modelFromProvider(provider) {
  return resolveImageProvider(provider)?.model || "";
}

function latestGenerationModel() {
  const generation = generations.find((item) => {
    const route = item?.model_route || {};
    return route.request_model || route.model || item.image_model;
  });
  const route = generation?.model_route || {};
  if (route.mode === "external_api") {
    return route.model || route.request_model || generation?.image_model || "";
  }
  return route.request_model || route.model || generation?.image_model || "";
}

function restoreLastImageModelSelection(options = {}) {
  const api = apiSettings.api || {};
  const candidates = [
    storedImageModel(),
    api.model,
    modelFromProvider(api.provider),
    latestGenerationModel(),
  ];
  const restored = candidates.some((candidate) => setModelSelectValue(candidate, { persist: true }));
  if (!restored) {
    persistSelectedImageModel();
  }
  if (options.announce && restored) {
    apiStatus.textContent = `已恢复上次模型：${selectedImageModelLabel()}`;
  }
  return restored;
}

function rememberModelFromRoute(route) {
  if (!route) return false;
  const routeModel = route.mode === "external_api" ? (route.model || route.request_model || "") : (route.request_model || route.model || "");
  if (setModelSelectValue(routeModel, { persist: true })) {
    return true;
  }
  return setModelSelectValue(modelFromProvider(route.provider), { persist: true });
}

async function openAccountCenter() {
  const willOpen = accountPopover.hidden;
  accountPopover.hidden = !willOpen;
  accountCenterButton.classList.toggle("active", willOpen);
  if (!willOpen) return;
  renderApiSettingsPanel();
  apiStatus.textContent = "个人中心设置已打开";
  await loadApiSettings();
}

function renderApiSettingsPanel() {
  const apiRoot = apiSettings.api || {};
  const selectedProvider = resolveImageProvider(apiRoot.provider);
  const api = {
    ...apiRoot,
    ...apiProfileForProvider(apiRoot, selectedProvider.provider),
    provider: selectedProvider.provider,
  };
  const isKlingProvider = selectedProvider.provider === "kling";
  const isFalProvider = selectedProvider.provider === "fal";
  const isFluxProvider = selectedProvider.provider === "flux";
  const authConfigured = api.auth_configured || api.api_key_set || (api.access_key_set && api.secret_key_set);
  const keyPlaceholder = api.api_key_set ? `已保存：${api.api_key_masked || "••••"}` : "输入 API Key";
  const accessKeyPlaceholder = api.access_key_set ? `已保存：${api.access_key_masked || "••••"}` : "可灵 Access Key";
  const secretKeyPlaceholder = api.secret_key_set ? `已保存：${api.secret_key_masked || "••••"}` : "可灵 Secret Key";
  const lastTest = api.last_test;
  const testText = lastTest?.message || "尚未测试";
  const selectedHealth = providerStatusFor(selectedProvider.provider);
  const remoteText = selectedHealth
    ? `${providerRemoteStatusLabel(selectedHealth.remote_status)} · ${selectedHealth.note || ""}`
    : "真实生成健康未读取";
  accountPopoverBody.innerHTML = `
    <div class="api-status-band account-status-band">
      <strong>${escapeHtml(accountState.label || "免费版")} · ${escapeHtml(accountState.user_segment || "普通用户")}</strong>
      <span>剩余 ${Number(accountState.credits_remaining || 0)} / ${Number(accountState.monthly_credits || 0)} 点 · 已用 ${Number(accountState.credits_used || 0)} 点</span>
    </div>
    <div class="workspace-panel-head">
      <strong>API 设置</strong>
      <span>本地保存</span>
    </div>
    <form class="api-settings-form" id="apiSettingsForm">
      <div class="api-status-band">
        <strong>${authConfigured ? "本地配置已保存" : "API 未配置"}</strong>
        <span id="apiProviderSummary">${escapeHtml(selectedProvider.display)} · 本地：${escapeHtml(testText)} · 远端：${escapeHtml(remoteText)}</span>
      </div>
      <div class="api-settings-grid">
        <label class="check-row full-span">
          <input type="checkbox" id="apiEnabledInput" ${api.enabled ? "checked" : ""} />
          <span>启用外部生成 API</span>
        </label>
        <label class="control-field">
          <span>服务商</span>
          <select id="apiProviderInput">
            ${apiProviderOptions(api.provider)}
          </select>
        </label>
        <label class="control-field">
          <span>模型</span>
          <input id="apiModelInput" type="text" value="${escapeAttribute(api.model || "")}" placeholder="填写模型名" />
        </label>
        <label class="control-field full-span">
          <span>Base URL</span>
          <input id="apiBaseUrlInput" type="text" value="${escapeAttribute(api.base_url || "")}" placeholder="https://.../v1" />
        </label>
          <label class="control-field full-span">
            <span>API Key</span>
            <input id="apiKeyInput" type="password" autocomplete="off" placeholder="${escapeAttribute(keyPlaceholder)}" />
          </label>
        ${isFalProvider ? `
          <p class="api-settings-note full-span">fal.ai 使用 API Key 认证；Base URL 填 https://fal.run，模型填 fal-ai/flux-pro/v1.1-ultra。参考人脸会作为 image_url 参与一致性约束。</p>
        ` : ""}
        ${isFluxProvider ? `
          <p class="api-settings-note full-span">FLUX / BFL 使用官方异步 API；Base URL 填 https://api.bfl.ai/v1，模型填 flux-2-max。文生图与参考图图生图都已接入真实生成。</p>
        ` : ""}
        ${isKlingProvider ? `
          <label class="control-field">
            <span>Access Key</span>
            <input id="apiAccessKeyInput" type="password" autocomplete="off" placeholder="${escapeAttribute(accessKeyPlaceholder)}" />
          </label>
          <label class="control-field">
            <span>Secret Key</span>
            <input id="apiSecretKeyInput" type="password" autocomplete="off" placeholder="${escapeAttribute(secretKeyPlaceholder)}" />
          </label>
          <p class="api-settings-note full-span">可灵支持直接填写 API Key；也可以填写 Access Key + Secret Key，本地会为请求生成 JWT。</p>
        ` : ""}
      </div>
      ${providerHealthRowsMarkup(providerStatus)}
      <div class="api-action-row">
        <button class="secondary-button" type="button" data-api-action="save">保存设置</button>
        <button class="secondary-button" type="button" data-api-action="test">检查配置</button>
        <button class="secondary-button danger-action" type="button" data-api-action="clear-key">清除凭证</button>
      </div>
    </form>
  `;
  wireApiSettingsForm();
}

function hideAccountCenter() {
  accountPopover.hidden = true;
  accountCenterButton.classList.remove("active");
}

function apiProviderOptions(selectedProvider) {
  const normalizedProvider = normalizeImageProvider(selectedProvider);
  return imageModelPresets.map((provider) => `
    <option value="${provider.provider}" ${provider.provider === normalizedProvider ? "selected" : ""}>${provider.display}</option>
  `).join("");
}

function normalizeImageProvider(provider) {
  if (provider === "openai-compatible") return "openai";
  if (provider === "stability") return "stable-diffusion";
  const knownProvider = imageModelPresets.find((item) => item.provider === provider);
  return knownProvider ? knownProvider.provider : "custom";
}

function resolveImageProvider(provider) {
  const normalizedProvider = normalizeImageProvider(provider);
  return imageModelPresets.find((item) => item.provider === normalizedProvider) || imageModelPresets.at(-1);
}

function apiProfileForProvider(apiRoot, provider) {
  const profiles = apiRoot?.profiles || {};
  const normalizedProvider = normalizeImageProvider(provider);
  return profiles[provider] || profiles[normalizedProvider] || (
    normalizeImageProvider(apiRoot?.provider) === normalizedProvider ? apiRoot : {}
  );
}

function providerStatusFor(provider) {
  const normalizedProvider = normalizeImageProvider(provider);
  return (providerStatus.providers || []).find((item) => normalizeImageProvider(item.provider) === normalizedProvider) || null;
}

function providerLocalStatusLabel(status) {
  return {
    ready: "本地配置完整",
    incomplete: "本地配置缺失",
  }[status] || localizeLabel(status || "未知");
}

function providerRemoteStatusLabel(status) {
  return {
    passed: "真实生成通过",
    failed: "远端失败",
    untested: "未实测",
    not_configured: "未配置",
  }[status] || localizeLabel(status || "未知");
}

function providerHealthRowsMarkup(health) {
  const providers = Array.isArray(health?.providers) ? health.providers : [];
  if (!providers.length) {
    return `
      <div class="provider-health-list">
        <div class="provider-health-empty">Provider 健康未读取</div>
      </div>
    `;
  }
  return `
    <div class="provider-health-list">
      ${providers.map(providerHealthRow).join("")}
    </div>
  `;
}

function providerHealthRow(provider) {
  const missing = Array.isArray(provider.missing) ? provider.missing : [];
  const localText = provider.local_status === "ready"
    ? providerLocalStatusLabel(provider.local_status)
    : `${providerLocalStatusLabel(provider.local_status)}：${missing.join("、") || "未启用"}`;
  const remoteText = providerRemoteStatusLabel(provider.remote_status);
  const lastEvent = provider.last_failure?.id
    ? `失败任务 ${provider.last_failure.id}`
    : provider.last_success?.id
      ? `成功 ${provider.last_success.id}${provider.last_success.size ? ` · ${provider.last_success.size}` : ""}`
      : "暂无真实生成记录";
  const credential = provider.credential_masked ? `凭证 ${provider.credential_masked}` : "无凭证";
  return `
    <article class="provider-health-row is-${escapeAttribute(provider.remote_status || "not_configured")}">
      <div>
        <strong>${escapeHtml(provider.label || provider.provider || "Provider")}</strong>
        <span>${escapeHtml(provider.model || "未填写模型")}</span>
      </div>
      <div>
        <span>${escapeHtml(localText)} · ${escapeHtml(credential)}</span>
        <small>${escapeHtml(provider.note || lastEvent)}</small>
      </div>
      <span>${escapeHtml(remoteText)}</span>
    </article>
  `;
}

function wireApiSettingsForm() {
  const providerInput = accountPopoverBody.querySelector("#apiProviderInput");
  providerInput?.addEventListener("change", () => {
    applyApiProviderPreset(providerInput.value);
  });
}

function applyApiProviderPreset(provider) {
  const preset = resolveImageProvider(provider);
  const currentRoot = apiSettings.api || {};
  const savedProfile = apiProfileForProvider(currentRoot, preset.provider);
  const modelInput = accountPopoverBody.querySelector("#apiModelInput");
  const baseUrlInput = accountPopoverBody.querySelector("#apiBaseUrlInput");
  const providerSummary = accountPopoverBody.querySelector("#apiProviderSummary");
  const model = savedProfile.model || preset.model;
  const baseUrl = savedProfile.base_url || preset.baseUrl;
  if (modelInput) {
    modelInput.value = model;
  }
  if (baseUrlInput) {
    baseUrlInput.value = baseUrl;
  }
  if (providerSummary) {
    const providerHealth = providerStatusFor(preset.provider);
    const remoteText = providerHealth ? providerRemoteStatusLabel(providerHealth.remote_status) : "远端未读取";
    providerSummary.textContent = `${preset.display} · 本地：${savedProfile.auth_configured ? "已保存" : "未保存"} · 远端：${remoteText}`;
  }
  apiSettings = {
    api: {
      profiles: currentRoot.profiles || {},
      api_key_set: false,
      api_key_masked: "",
      access_key_set: false,
      access_key_masked: "",
      secret_key_set: false,
      secret_key_masked: "",
      auth_configured: false,
      last_test: null,
      ...savedProfile,
      enabled: accountPopoverBody.querySelector("#apiEnabledInput")?.checked || false,
      provider: preset.provider,
      model,
      base_url: baseUrl,
    },
  };
  setModelSelectValue(model, { persist: true });
  renderApiSettingsPanel();
  apiStatus.textContent = `已选择 ${preset.display}`;
}

async function saveApiSettings(options = {}) {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能保存 API";
    return false;
  }
  const formRoot = accountPopoverBody;
  const keyInput = formRoot.querySelector("#apiKeyInput");
  const accessKeyInput = formRoot.querySelector("#apiAccessKeyInput");
  const secretKeyInput = formRoot.querySelector("#apiSecretKeyInput");
  const body = {
    api: {
      enabled: formRoot.querySelector("#apiEnabledInput")?.checked || false,
      provider: formRoot.querySelector("#apiProviderInput")?.value || "openai",
      base_url: formRoot.querySelector("#apiBaseUrlInput")?.value || "",
      model: formRoot.querySelector("#apiModelInput")?.value || "",
      clear_api_key: options.clearKey === true,
      clear_access_key: options.clearKey === true,
      clear_secret_key: options.clearKey === true,
    },
  };
  const apiKey = keyInput?.value?.trim();
  if (apiKey) {
    body.api.api_key = apiKey;
  }
  const accessKey = accessKeyInput?.value?.trim();
  if (accessKey) {
    body.api.access_key = accessKey;
  }
  const secretKey = secretKeyInput?.value?.trim();
  if (secretKey) {
    body.api.secret_key = secretKey;
  }

  try {
    const response = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    apiSettings = payload.settings || apiSettings;
    await loadProviderStatus();
    updateProfileApiStatus();
    restoreLastImageModelSelection();
    renderApiSettingsPanel();
    if (!options.silent) {
      apiStatus.textContent = options.clearKey ? "API 凭证已清除" : "API 设置已保存";
    }
    return true;
  } catch (error) {
    apiStatus.textContent = error.message;
    return false;
  }
}

async function testApiSettings() {
  const saved = await saveApiSettings({ silent: true });
  if (!saved) return;
  try {
    const response = await fetch("/api/settings/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    apiSettings = payload.settings || apiSettings;
    await loadProviderStatus();
    updateProfileApiStatus();
    renderApiSettingsPanel();
    apiStatus.textContent = payload.test?.message || "API 配置测试完成";
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

function updateProfileApiStatus() {
  const api = apiSettings.api || {};
  const authConfigured = api.auth_configured || api.api_key_set || (api.access_key_set && api.secret_key_set);
  const maskedCredential = api.api_key_masked || api.access_key_masked || "已保存";
  if (!apiAvailable) {
    profileApiStatus.textContent = "后端未连接";
    return;
  }
  if (api.enabled && authConfigured) {
    profileApiStatus.textContent = `API 已配置 · ${maskedCredential}`;
    return;
  }
  if (authConfigured) {
    profileApiStatus.textContent = `API 已保存 · 未启用`;
    return;
  }
  profileApiStatus.textContent = "API 未配置";
}

function renderCharacterList() {
  characterList.replaceChildren(
    ...characters.map((character) => {
      const row = document.createElement("div");
      row.className = `character-row${character.id === activeCharacterId ? " active" : ""}`;
      row.dataset.character = character.id;

      const selectButton = document.createElement("button");
      selectButton.className = "character-select";
      selectButton.type = "button";
      selectButton.addEventListener("click", () => {
        activeCharacterId = character.id;
        setCharacter(character.id);
        renderCharacterList();
        renderGenerationGrid();
        refreshOpenVersionHistory();
      });

      const thumb = document.createElement("span");
      thumb.className = `row-thumb ${presetClass(character.style.preset)}`.trim();

      const text = document.createElement("span");
      const name = document.createElement("strong");
      name.textContent = character.name;
      const meta = document.createElement("small");
      meta.textContent = `${labelForPreset(character.style.preset)} · ${character.consistency_percent}% · ${lastUsedLabel(character.asset_summary?.last_used_at)}`;
      meta.title = assetMetaForCharacter(character);
      text.append(name, meta);

      const deleteButton = document.createElement("button");
      deleteButton.className = "character-delete";
      deleteButton.type = "button";
      deleteButton.textContent = "×";
      deleteButton.setAttribute("aria-label", `删除角色 ${character.name}`);
      deleteButton.disabled = characters.length <= 1;
      deleteButton.addEventListener("click", async (event) => {
        event.stopPropagation();
        await confirmBeforeDelete({
          key: `character:${character.id}`,
          button: deleteButton,
          idleLabel: `删除角色 ${character.name}`,
          confirmLabel: `确认删除角色 ${character.name}`,
          statusText: `再次点击确认删除角色：${character.name}`,
          onConfirm: () => deleteCharacter(character.id),
        });
      });

      selectButton.append(thumb, text);
      row.append(selectButton, deleteButton);
      return row;
    }),
  );
}

function clearPendingDeleteConfirmation() {
  if (!pendingDeleteConfirmation) return;
  const { button, idleText, idleLabel, timeoutId } = pendingDeleteConfirmation;
  window.clearTimeout(timeoutId);
  if (button?.isConnected) {
    button.classList.remove("is-confirming");
    button.textContent = idleText;
    if (idleLabel) {
      button.setAttribute("aria-label", idleLabel);
    }
  }
  pendingDeleteConfirmation = null;
}

async function confirmBeforeDelete({
  key,
  button,
  idleText = "×",
  confirmText = "确认",
  idleLabel,
  confirmLabel,
  statusText,
  onConfirm,
}) {
  if (!button || button.disabled) return;

  if (pendingDeleteConfirmation?.key === key) {
    clearPendingDeleteConfirmation();
    await onConfirm();
    return;
  }

  clearPendingDeleteConfirmation();
  button.classList.add("is-confirming");
  button.textContent = confirmText;
  if (confirmLabel) {
    button.setAttribute("aria-label", confirmLabel);
  }
  apiStatus.textContent = statusText || "再次点击确认删除";
  const timeoutId = window.setTimeout(clearPendingDeleteConfirmation, 6000);
  pendingDeleteConfirmation = { key, button, idleText, idleLabel, timeoutId };
}

function setCharacter(characterId) {
  const character = characters.find((item) => item.id === characterId) || characters[0];
  activeCharacterId = character.id;
  characterName.textContent = character.name;
  consistencyScore.textContent = `${character.consistency_percent}%`;
  versionBadge.textContent = `v${character.version || 1}`;
  if (lastUsedBadge) {
    lastUsedBadge.textContent = lastUsedLabel(character.asset_summary?.last_used_at);
  }
  if (activeCharacterThumb) {
    activeCharacterThumb.className = `row-thumb large ${presetClass(character.style.preset)}`.trim();
  }
  promptInput.value = character.prompt || promptInput.value;
  updatePromptCounters();
  syncIdentity(Math.max(character.identity_strength, 0.85));
  applyLoraSelection(character.style?.lora?.id || loraSelect.value || "portrait-consistency", false, character.style?.lora?.weight);
  stylePills.replaceChildren(...character.style_labels.map((style) => pill(style)));
  memoryList.replaceChildren(...character.memory_labels.map((memory) => pill(memory)));
  renderMemoryInsights(character);
  setActiveStyleFromPreset(character.style.preset, character.style?.lora?.id);
  applyCharacterReferenceAssets(character);
  applyCharacterReferenceCollections(character);
  renderIdentityReadiness(character.identity_readiness);
}

async function generateConditioning() {
  if (isCharacterPromptSubject(promptSubjectHint(promptInput.value))) {
    enforceIdentityMargin();
  }
  const requestedCount = Number(getCheckedValue("count"));
  persistSelectedImageModel();
  appShell.classList.add("is-generating");
  generateButton.textContent = "生成中";
  showGenerationInProgress(requestedCount);

  if (!apiAvailable) {
    window.setTimeout(() => {
      appShell.classList.remove("is-generating");
      updateGenerateSummary();
      apiStatus.textContent = "本地预览模式";
      showGenerationNotice("error", "后端未连接", "当前是静态预览，不能保存新的生成图");
    }, 600);
    return;
  }

  try {
    const response = await fetch("/api/generations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(generationRequestPayload(requestedCount)),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }

    const created = payload.generations || [];
    const job = payload.job || {};
    if (payload.account) {
      setAccountState(payload.account);
    }
    generations = [...created, ...generations];
    if (job.id) {
      generationJobs = [job, ...generationJobs.filter((item) => item.id !== job.id)];
    }
    latestGenerationIds = new Set(created.map((generation) => generation.id).filter(Boolean));
    showGenerationResultsAfterCreate();
    renderGenerationGrid();
    const driftRisk = created[0]?.drift_risk || "unknown";
    const route = created[0]?.model_route;
    rememberModelFromRoute(route);
    const routeText = shortModelRouteLabel(route);
    const jobText = job.id ? `任务 ${job.id}` : "任务未记录";
    const statusText = `已生成 ${created.length} 张 · ${jobText} · ${routeText} · 漂移风险：${labelForDrift(driftRisk)} · ${qualitySummary(created)}`;
    apiStatus.textContent = statusText;
    if (route?.real_generation) {
      showGenerationNotice("success", "真实 API 已生成", `${jobText} · 新增 ${created.length} 张图片，已置顶显示`);
    } else if (route?.mode === "external_api") {
      const fallbackReason = providerHasRealGenerationRoute(route.provider)
        ? `${route.provider_label || "该服务商"} 已接入，本次使用本地预览，未消耗外部 API`
        : `${route.provider_label || "该服务商"} 暂未接入真实生成，本次未消耗外部 API`;
      showGenerationNotice("success", "本地预览已生成", `${jobText} · ${fallbackReason}`);
    } else {
      showGenerationNotice("success", "本地预览已生成", `${jobText} · 新增 ${created.length} 张图片，已置顶显示`);
    }
    outputGrid.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) {
    if (apiAvailable) {
      try {
        await loadGenerationJobs();
      } catch (_refreshError) {
        // Keep the original generation error visible.
      }
    }
    apiStatus.textContent = error.message;
    showGenerationNotice("error", "生成失败", error.message || "请检查后端服务或 API 设置");
    renderGenerationGrid();
  } finally {
    appShell.classList.remove("is-generating");
    outputGrid.removeAttribute("aria-busy");
    updateGenerateSummary();
  }
}

function showGenerationInProgress(count) {
  showGenerationResultsPanel();
  latestGenerationIds = new Set();
  const placeholders = Array.from({ length: Math.max(1, count) }, (_, index) => generationPlaceholderTile(index, count));
  outputGrid.replaceChildren(...placeholders);
  outputGrid.setAttribute("aria-busy", "true");
  showGenerationNotice("loading", "正在生成", `正在生成 ${count} 张图片，完成后会出现在右侧第一排`);
}

function showGenerationResultsAfterCreate() {
  showGenerationResultsPanel();
}

function showGenerationResultsPanel() {
  if (favoritesOnly.checked) {
    favoritesOnly.checked = false;
  }
  setActiveNavByName("首页");
  workspaceTitle.textContent = "生成结果";
  showResultSurface();
}

function showResultSurface({ keepWorkspacePanel = false, hideNotice = false } = {}) {
  workspaceModePanel.hidden = !keepWorkspacePanel;
  // When the mode panel is shown ALONGSIDE the works grid (我的作品), it must sit
  // as a band above the grid, not share the grid's row (which makes them split
  // into two columns). The band class moves it to row 2.
  workspaceModePanel.classList.toggle("is-works-band", keepWorkspacePanel);
  outputGrid.hidden = false;
  if (referenceRail) {
    referenceRail.hidden = false;
  }
  if (hideNotice && generationNotice) {
    generationNotice.hidden = true;
  }
}

function showWorkspaceSurface(title) {
  if (title) {
    workspaceTitle.textContent = title;
  }
  workspaceModePanel.hidden = false;
  workspaceModePanel.classList.remove("is-works-band");
  outputGrid.hidden = true;
  outputGrid.removeAttribute("aria-busy");
  if (referenceRail) {
    referenceRail.hidden = true;
  }
  if (generationNotice) {
    generationNotice.hidden = true;
  }
}

function showGenerationNotice(type, title, message) {
  if (!generationNotice) return;
  generationNotice.hidden = false;
  generationNotice.className = `generation-notice is-${type}`;
  const titleNode = document.createElement("strong");
  titleNode.textContent = title;
  const messageNode = document.createElement("span");
  messageNode.textContent = message;
  generationNotice.replaceChildren(titleNode, messageNode);
}

async function createCharacter() {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能新建角色";
    return;
  }
  createCharacterButton.disabled = true;
  try {
    const nextIndex = characters.filter((character) => character.name.startsWith("新角色")).length + 1;
    const name = nextIndex === 1 ? "新角色" : `新角色 ${nextIndex}`;
    const response = await fetch("/api/characters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        style: {
          preset: "cinematic",
          prompt: "cinematic portrait soft daylight",
          lora_id: loraSelect.value,
          lora_weight: Number(loraRange.value),
        },
        prompt: `${name}，一致性角色肖像，锁定身份，柔和日光`,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const created = normalizeCharacter(payload.character);
    characters = [...characters, created];
    activeCharacterId = created.id;
    renderCharacterList();
    setCharacter(created.id);
    apiStatus.textContent = `${created.name} 已创建`;
  } catch (error) {
    apiStatus.textContent = error.message;
  } finally {
    createCharacterButton.disabled = false;
  }
}

function showCharacterEditor() {
  const character = characters.find((item) => item.id === activeCharacterId);
  if (!character) return;
  const summary = character.asset_summary || {};
  setActiveNavByName("首页");
  showWorkspaceSurface("角色资料");
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <strong>${escapeHtml(character.name)} 角色资料</strong>
      <span>${assetMetaForCharacter(character)}</span>
    </div>
    <form class="character-profile-form" id="characterEditForm">
      <div class="asset-summary-grid">
        <span>一致性 ${character.consistency_percent}%</span>
        <span>版本 ${Number(summary.version_count || character.version || 1)}</span>
        <span>参考图 ${Number(summary.reference_count || 0)}</span>
        <span>生成图 ${Number(summary.generation_count || 0)}</span>
        <span>收藏 ${Number(summary.favorite_count || 0)}</span>
        <span>${lastUsedLabel(summary.last_used_at)}</span>
      </div>
      <label class="control-field">
        <span>角色名称</span>
        <input id="characterEditName" type="text" maxlength="40" value="${escapeAttribute(character.name)}" />
      </label>
      <label class="control-field full-span">
        <span>默认提示词</span>
        <textarea id="characterEditPrompt" maxlength="1000">${escapeHtml(character.prompt || "")}</textarea>
      </label>
      <label class="control-field">
        <span>角色标签</span>
        <input id="characterEditTags" type="text" maxlength="160" value="${escapeAttribute((character.tags || []).join("，"))}" />
      </label>
      <label class="control-field">
        <span>默认风格</span>
        <select id="characterEditStyle">
          ${characterStyleOptions(character.style?.preset)}
        </select>
      </label>
      <label class="control-field">
        <span>默认 LoRA</span>
        <select id="characterEditLora">
          ${characterLoraOptions(character.style?.lora?.id)}
        </select>
      </label>
      <label class="control-field">
        <span>LoRA 权重</span>
        <input id="characterEditLoraWeight" type="number" min="0" max="1" step="0.01" value="${Number(character.style?.lora?.weight ?? loraRange.value ?? 0.72).toFixed(2)}" />
      </label>
      <div class="project-review-actions">
        <button class="secondary-button" type="submit">保存资料</button>
        <button class="secondary-button" type="button" data-workspace-action="cancel-character-edit">取消</button>
      </div>
    </form>
  `;
  apiStatus.textContent = "角色资料编辑已打开";
}

async function saveCharacterProfile() {
  const character = characters.find((item) => item.id === activeCharacterId);
  if (!character) return;
  const formRoot = workspaceModePanel.querySelector("#characterEditForm");
  const stylePreset = formRoot.querySelector("#characterEditStyle")?.value || character.style?.preset || "cinematic";
  const body = {
    name: formRoot.querySelector("#characterEditName")?.value || character.name,
    prompt: formRoot.querySelector("#characterEditPrompt")?.value || character.prompt || "",
    tags: formRoot.querySelector("#characterEditTags")?.value || "",
    style: {
      preset: stylePreset,
      prompt: stylePromptForPreset(stylePreset),
      lora_id: formRoot.querySelector("#characterEditLora")?.value || character.style?.lora?.id || loraSelect.value,
      lora_weight: Number(formRoot.querySelector("#characterEditLoraWeight")?.value || character.style?.lora?.weight || loraRange.value || 0.72),
    },
  };

  if (!apiAvailable) {
    const updated = normalizeCharacter({
      ...character,
      ...body,
      style: { preset: stylePreset, lora: { id: body.style.lora_id, weight: body.style.lora_weight } },
      tags: normalizeTagInput(body.tags),
    });
    characters = characters.map((item) => (item.id === updated.id ? updated : item));
    setCharacter(updated.id);
    renderCharacterList();
    showCharacterEditor();
    apiStatus.textContent = `${updated.name} 资料已更新`;
    return;
  }

  try {
    const response = await fetch(`/api/characters/${activeCharacterId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const updated = normalizeCharacter(payload.character);
    characters = characters.map((item) => (item.id === updated.id ? updated : item));
    setCharacter(updated.id);
    renderCharacterList();
    showCharacterEditor();
    apiStatus.textContent = `${updated.name} 资料已保存`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

function characterStyleOptions(selectedPreset = "cinematic") {
  return [
    ["cinematic", "写真 / 电影人像"],
    ["anime", "动漫 / 干净线条"],
    ["commercial", "商业 / 品牌广告"],
  ].map(([value, label]) => `
    <option value="${value}" ${value === selectedPreset ? "selected" : ""}>${label}</option>
  `).join("");
}

function characterLoraOptions(selectedLora = "portrait-consistency") {
  return loras.map((lora) => `
    <option value="${escapeAttribute(lora.id)}" ${lora.id === selectedLora ? "selected" : ""}>${escapeHtml(lora.label || lora.name)}</option>
  `).join("");
}

function stylePromptForPreset(preset) {
  if (preset === "anime") return "anime clean line soft bloom";
  if (preset === "commercial") return "commercial product advertising studio key light premium campaign poster";
  return "cinematic portrait soft daylight 50mm";
}

function normalizeTagInput(value) {
  return String(value || "")
    .split(/[,，、\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item, index, all) => all.indexOf(item) === index)
    .slice(0, 12);
}

async function deleteCharacter(characterId) {
  if (characters.length <= 1) {
    apiStatus.textContent = "至少保留一个角色";
    return;
  }
  const character = characters.find((item) => item.id === characterId);
  if (!character) return;

  if (!apiAvailable) {
    characters = characters.filter((item) => item.id !== characterId);
    generations = generations.filter((generation) => generation.character_id !== characterId);
    projects = projects.map((project) => ({
      ...project,
      character_ids: (project.character_ids || []).filter((id) => id !== characterId),
    }));
    activeCharacterId = characters[0].id;
    renderCharacterList();
    setCharacter(activeCharacterId);
    renderGenerationGrid();
    await refreshOpenVersionHistory();
    if (workspaceTitle.textContent === "项目") {
      renderProjectsPanel();
    }
    apiStatus.textContent = `${character.name} 已删除`;
    return;
  }

  try {
    const response = await fetch(`/api/characters/${characterId}`, { method: "DELETE" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `删除失败：${response.status}`);
    }
    characters = (payload.characters || []).map(normalizeCharacter);
    await loadGenerations();
    await loadProjects();
    if (!characters.some((item) => item.id === activeCharacterId)) {
      activeCharacterId = characters[0]?.id || "";
    }
    renderCharacterList();
    setCharacter(activeCharacterId);
    renderGenerationGrid();
    await refreshOpenVersionHistory();
    if (!projects.some((project) => project.id === activeProjectId)) {
      activeProjectId = projects[0]?.id || "";
    }
    if (workspaceTitle.textContent === "项目") {
      renderProjectsPanel();
    }
    apiStatus.textContent = `${payload.deleted?.name || character.name} 已删除`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function trainMore() {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能继续训练";
    return;
  }
  trainMoreButton.disabled = true;
  try {
    const character = characters.find((item) => item.id === activeCharacterId);
    const nextVersion = (character?.version || 1) + 1;
    const response = await fetch(`/api/characters/${activeCharacterId}/versions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        note: `继续训练 v${nextVersion}`,
        style: {
          preset: character?.style?.preset || "cinematic",
          prompt: stylePills.firstElementChild?.textContent || "cinematic portrait",
          lora_id: loraSelect.value,
          lora_weight: Number(loraRange.value),
        },
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const updated = normalizeCharacter(payload.character);
    characters = characters.map((item) => (item.id === updated.id ? updated : item));
    setCharacter(updated.id);
    renderCharacterList();
    await refreshOpenVersionHistory();
    apiStatus.textContent = `${updated.name} 已训练到 v${updated.version}`;
  } catch (error) {
    apiStatus.textContent = error.message;
  } finally {
    trainMoreButton.disabled = false;
  }
}

async function showVersions() {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能查看版本";
    return;
  }
  try {
    const response = await fetch(`/api/characters/${activeCharacterId}/versions`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const versions = payload.versions || [];
    renderVersionHistoryPanel(versions);
    apiStatus.textContent = versions.length ? `已打开 ${versions.length} 个版本` : "暂无版本";
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function refreshOpenVersionHistory() {
  if (!apiAvailable || workspaceTitle.textContent !== "版本历史") return;
  try {
    const response = await fetch(`/api/characters/${activeCharacterId}/versions`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    renderVersionHistoryPanel(payload.versions || []);
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function toggleFavorite(generationId) {
  const generation = generations.find((item) => item.id === generationId);
  if (!generation) return;

  if (!apiAvailable) {
    generation.favorite = !generation.favorite;
    renderGenerationGrid();
    return generation;
  }

  const response = await fetch(`/api/generations/${generationId}/favorite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ favorite: !generation.favorite }),
  });
  if (!response.ok) return null;
  const payload = await response.json();
  generations = generations.map((item) => (item.id === generationId ? payload.generation : item));
  renderGenerationGrid();
  return payload.generation;
}

async function deleteGeneration(generationId) {
  if (!apiAvailable) {
    generations = generations.filter((item) => item.id !== generationId);
    latestGenerationIds.delete(generationId);
    renderGenerationGrid();
    apiStatus.textContent = "本地生成图已删除";
    return;
  }

  try {
    const response = await fetch(`/api/generations/${generationId}`, { method: "DELETE" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `删除失败：${response.status}`);
    }
    generations = payload.generations || generations.filter((item) => item.id !== generationId);
    generationJobs = payload.jobs || generationJobs.map((job) => (
      (job.generation_ids || []).includes(generationId)
        ? {
            ...job,
            generation_ids: (job.generation_ids || []).filter((id) => id !== generationId),
            deleted_generation_ids: [...new Set([...(job.deleted_generation_ids || []), generationId])],
          }
        : job
    ));
    if (Array.isArray(payload.characters)) {
      const currentPrompt = promptInput.value;
      const currentNegativePrompt = negativePromptInput.value;
      characters = payload.characters.map(normalizeCharacter);
      setCharacter(activeCharacterId);
      promptInput.value = currentPrompt;
      negativePromptInput.value = currentNegativePrompt;
      updatePromptCounters();
    }
    latestGenerationIds.delete(generationId);
    renderGenerationGrid();
    apiStatus.textContent = `生成图已删除：${generationId}`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function exportProject() {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能导出";
    return;
  }
  try {
    const response = await fetch("/api/export");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const project = {
      ...payload.project,
      demo_subscription: currentPlanExport(),
    };
    downloadJson(project, "persona-studio-export.json");
    apiStatus.textContent = `导出完成 · ${project.counts.generations} 张生成图`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

function syncIdentity(value) {
  const displayValue = Number(value).toFixed(2);
  detailIdentity.value = displayValue;
  identityRange.value = displayValue;
  detailIdentityValue.textContent = displayValue;
  identityValue.textContent = displayValue;
  identityValue.value = displayValue;
  identityValue.setAttribute("aria-label", `相似度权重 ${displayValue}`);
}

function syncStyle(value) {
  const displayValue = Number(value).toFixed(2);
  styleRange.value = displayValue;
  styleValue.textContent = displayValue;
  styleValue.value = displayValue;
  styleValue.setAttribute("aria-label", `风格权重 ${displayValue}`);
}

function enforceIdentityMargin() {
  const currentIdentity = Number(identityRange.value);
  const currentStyle = Number(styleRange.value);
  let targetIdentity = Math.max(0.9, currentIdentity);
  let targetStyle = currentStyle;

  if (targetIdentity - targetStyle < 0.2) {
    targetIdentity = Math.min(0.95, Math.max(targetIdentity, targetStyle + 0.2));
  }

  if (targetIdentity - targetStyle < 0.2) {
    targetStyle = Math.max(0.2, targetIdentity - 0.2);
  }

  syncIdentity(targetIdentity);
  syncStyle(targetStyle);
}

async function diagnoseFusionConditioning() {
  fusionPanel.hidden = false;
  fusionPanel.className = "fusion-panel is-loading";
  fusionPanel.innerHTML = `<strong>融合诊断中</strong><span>正在编译身份、风格、提示词和状态权重。</span>`;

  if (!apiAvailable) {
    renderFusionError("需要后端连接才能诊断融合条件包");
    return;
  }

  if (Number(identityRange.value) <= Number(styleRange.value)) {
    const message = "身份权重必须高于风格权重，否则会漂脸";
    renderFusionError(message);
    apiStatus.textContent = message;
    return;
  }

  try {
    const response = await fetch(`/api/characters/${activeCharacterId}/condition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: promptInput.value,
        state: stateSelect.value,
        identity_weight: Number(identityRange.value),
        style_weight: Number(styleRange.value),
        prompt_weight: 1.0,
        state_weight: 0.4,
        lora_id: loraSelect.value,
        lora_weight: Number(loraRange.value),
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `融合诊断失败：${response.status}`);
    }
    renderFusionPanel(payload.conditioning);
    apiStatus.textContent = `融合诊断完成 · 漂移风险 ${labelForDrift(payload.conditioning?.drift_risk)}`;
  } catch (error) {
    renderFusionError(error.message);
    apiStatus.textContent = error.message;
  }
}

function renderFusionPanel(conditioning) {
  const weights = conditioning?.weights || {};
  const diagnostics = conditioning?.diagnostics || {};
  const checks = Array.isArray(diagnostics.checks) ? diagnostics.checks : [];
  const risk = conditioning?.drift_risk || "unknown";
  const lora = diagnostics.lora_summary || conditioning?.lora || {};
  const controlnet = diagnostics.controlnet_summary || conditioning?.controlnet || {};
  fusionPanel.hidden = false;
  fusionPanel.className = `fusion-panel is-${risk}`;
  fusionPanel.innerHTML = `
    <div class="fusion-head">
      <strong>Fusion ${labelForDrift(risk)}</strong>
      <span>边距 ${formatWeight(diagnostics.identity_margin)} · ${conditioning?.vector_dim || 0} dim</span>
    </div>
    <div class="fusion-weight-grid">
      ${fusionWeightCell("身份", weights.identity)}
      ${fusionWeightCell("风格", weights.style)}
      ${fusionWeightCell("提示词", weights.prompt)}
      ${fusionWeightCell("状态", weights.state)}
    </div>
    <div class="fusion-check-list">
      ${checks.map((check) => fusionCheckRow(check)).join("")}
    </div>
    <div class="fusion-foot">
      <span>${escapeHtml(diagnostics.summary || "条件包已编译")}</span>
      <span>ControlNet 脸 ${formatWeight(controlnet.face_lock)} · 姿态 ${formatWeight(controlnet.pose_lock)} · 风格 ${formatWeight(controlnet.style_guidance)}</span>
      <span>LoRA ${escapeHtml(lora.label || lora.id || "未启用")} ${lora.weight === undefined ? "" : `· ${formatWeight(lora.weight)}`}</span>
    </div>
  `;
}

function fusionWeightCell(label, value) {
  const safeValue = Math.max(0, Math.min(1, Number(value || 0)));
  return `
    <span>
      <strong>${escapeHtml(label)}</strong>
      <i style="--weight:${Math.round(safeValue * 100)}%"></i>
      <em>${formatWeight(value)}</em>
    </span>
  `;
}

function fusionCheckRow(check) {
  return `
    <span class="fusion-check is-${escapeAttribute(check.status || "review")}">
      <strong>${escapeHtml(check.label || check.id || "检查项")}</strong>
      <em>${escapeHtml(fusionStatusLabel(check.status))} · ${formatWeight(check.value)}</em>
    </span>
  `;
}

function fusionStatusLabel(status) {
  if (status === "pass") return "通过";
  if (status === "fail") return "阻断";
  return "复核";
}

function formatWeight(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "0.00";
}

function renderFusionError(message) {
  fusionPanel.hidden = false;
  fusionPanel.className = "fusion-panel is-high";
  fusionPanel.innerHTML = `<strong>融合诊断失败</strong><span>${escapeHtml(message)}</span>`;
}

function generationRequestPayload(count = Number(getCheckedValue("count") || 4)) {
  return {
    character_id: activeCharacterId,
    mode: activeGenerationMode,
    prompt: promptInput.value,
    negative_prompt: negativePromptInput.value,
    state: stateSelect.value,
    pose_control: {
      pose: poseControlSelect.value,
      weight: 0.4,
    },
    identity_weight: Number(identityRange.value),
    style_weight: Number(styleRange.value),
    lora_id: loraSelect.value,
    lora_weight: Number(loraRange.value),
    image_model: modelSelect.value,
    image_model_label: selectedImageModelLabel(),
    reference_guidance: selectedReferenceGuidance(),
    count,
    size: getCheckedValue("size"),
  };
}

async function runGenerationPreflight() {
  if (isCharacterPromptSubject(promptSubjectHint(promptInput.value))) {
    enforceIdentityMargin();
  }
  showWorkspaceSurface("生成预检");
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>Generation Preflight</strong>
        <span>正在检查主体、尺寸、身份锁和参考图</span>
      </div>
    </div>
  `;

  if (!apiAvailable) {
    workspaceModePanel.innerHTML = `<div class="empty-state">需要后端连接才能运行生成预检</div>`;
    apiStatus.textContent = "后端未连接";
    return;
  }

  try {
    const response = await fetch("/api/generations/preflight", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(generationRequestPayload()),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `预检失败：${response.status}`);
    }
    renderGenerationPreflightPanel(payload.preflight);
    apiStatus.textContent = `生成预检：${preflightStatusLabel(payload.preflight?.status)} · ${payload.preflight?.subject_label || "主体"}`;
  } catch (error) {
    workspaceModePanel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    apiStatus.textContent = error.message;
  }
}

function renderGenerationPreflightPanel(preflight) {
  const checks = Array.isArray(preflight?.checks) ? preflight.checks : [];
  const size = preflight?.size || {};
  const references = preflight?.reference_counts || {};
  const pose = preflight?.pose_control || {};
  const billing = preflight?.billing || {};
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>${escapeHtml(preflight?.subject_label || "主体")} Preflight</strong>
        <span>${preflightStatusLabel(preflight?.status)} · ${escapeHtml(size.label || "3:4")} · ${escapeHtml(size.provider_size || "未映射")}</span>
      </div>
      <button class="secondary-button" type="button" data-workspace-action="generation-preflight">刷新</button>
    </div>
    <div class="preflight-summary is-${escapeAttribute(preflight?.status || "ready")}">
      <strong>${escapeHtml(preflightStatusLabel(preflight?.status))}</strong>
      <span>${escapeHtml(preflight?.summary || "预检完成")}</span>
    </div>
    <div class="preflight-grid">
      ${checks.map((check) => preflightCheckCard(check)).join("")}
    </div>
    <div class="preflight-meta">
      <span>身份锁：${preflight?.uses_identity_lock ? "启用" : "不启用"}</span>
      <span>姿态锁：${pose.enabled ? escapeHtml(pose.label || poseControlLabel(pose.pose)) : "自动"}</span>
      <span>身份边距：${preflight?.identity_margin === null || preflight?.identity_margin === undefined ? "不适用" : formatWeight(preflight.identity_margin)}</span>
      <span>参考图：${Number(references.effective || 0)}/${Number(references.requested || 0)} 生效</span>
      <span>额度：${billing.enough === false ? `不足 · 需 ${Number(billing.cost || 0)} 点 · 剩余 ${Number(billing.credits_remaining || 0)}` : `${Number(billing.cost || 0)} 点 · 剩余 ${Number(billing.credits_after ?? billing.credits_remaining ?? 0)}`}</span>
      <span>预览画布：${size.preview_canvas?.width || 0} x ${size.preview_canvas?.height || 0}</span>
    </div>
  `;
}

function preflightCheckCard(check) {
  return `
    <article class="preflight-check is-${escapeAttribute(check.status || "pass")}">
      <strong>${escapeHtml(check.label || check.id || "检查项")}</strong>
      <span>${escapeHtml(check.value || "")}</span>
    </article>
  `;
}

function preflightStatusLabel(status) {
  if (status === "blocked") return "阻断";
  if (status === "review") return "需复核";
  return "可生成";
}

async function showStyleAssetPanel() {
  showWorkspaceSurface("风格资产");
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>Style Model</strong>
        <span>正在编译风格向量</span>
      </div>
    </div>
  `;

  if (!apiAvailable) {
    workspaceModePanel.innerHTML = `<div class="empty-state">需要后端连接才能查看风格资产</div>`;
    apiStatus.textContent = "后端未连接";
    return;
  }

  try {
    const response = await fetch("/api/styles/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentStylePreviewPayload()),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `风格资产加载失败：${response.status}`);
    }
    renderStyleAssetPanel(payload.style);
    apiStatus.textContent = `风格资产已加载 · ${payload.style?.vector_dim || 0} dim`;
  } catch (error) {
    workspaceModePanel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    apiStatus.textContent = error.message;
  }
}

function openStyleLibrary() {
  activeStyleLibraryLabel = activeStyleLabel();
  styleLibraryOverlay.hidden = false;
  moreStylesButton.setAttribute("aria-expanded", "true");
  renderStyleLibrary();
  renderStyleLibraryDetail(activeStyleLibraryLabel);
  if (apiAvailable) {
    styleCatalog.forEach((item) => {
      void hydrateStyleLibraryProfile(item.label);
    });
  }
  closeStyleLibrary.focus();
  apiStatus.textContent = "风格库已打开";
}

function closeStyleLibraryDialog() {
  styleLibraryOverlay.hidden = true;
  moreStylesButton.setAttribute("aria-expanded", "false");
}

function selectStyleLibraryItem(label) {
  activeStyleLibraryLabel = styleCatalogItem(label)?.label || activeStyleLibraryLabel;
  renderStyleLibrary();
  renderStyleLibraryDetail(activeStyleLibraryLabel);
  void hydrateStyleLibraryProfile(activeStyleLibraryLabel);
}

function renderStyleLibrary() {
  styleLibraryGrid.innerHTML = styleCatalog.map((item) => styleLibraryCard(item)).join("");
}

function styleLibraryCard(item) {
  const active = item.label === activeStyleLibraryLabel;
  const cardParams = item.cardParams?.length ? item.cardParams : [
    { label: "强度", value: Number(item.styleWeight).toFixed(2) },
    { label: "适配器", value: loraForStyleItem(item).label || item.loraId },
    { label: "关键词", value: item.tokens?.[0] || item.preset },
  ];
  return `
    <article class="style-library-card ${active ? "active" : ""}">
      <button class="style-library-select" type="button" data-style-detail="${escapeAttribute(item.label)}" aria-pressed="${active ? "true" : "false"}">
        <span class="style-preview-frame is-style-asset ${escapeAttribute(item.imageClass)}">
          <img src="${escapeAttribute(item.image)}" alt="${escapeAttribute(item.label)}风格预览" />
        </span>
        <span class="style-library-card-title">
          <strong>${escapeHtml(item.label)}</strong>
          <small>${escapeHtml(item.summary || item.promptSnippet || item.label)}</small>
        </span>
        <dl class="style-card-params">
          ${cardParams.slice(0, 3).map((param) => `
            <div><dt>${escapeHtml(param.label)}</dt><dd>${escapeHtml(param.value)}</dd></div>
          `).join("")}
        </dl>
      </button>
      <button class="secondary-button style-card-apply" type="button" data-style-apply="${escapeAttribute(item.label)}">应用</button>
    </article>
  `;
}

function renderStyleLibraryDetail(label) {
  const item = styleCatalogItem(label);
  if (!item) return;
  const profile = styleLibraryProfiles[item.label];
  const controls = styleCatalogControlRows(item);
  const tokens = Array.isArray(item.tokens) && item.tokens.length
    ? item.tokens
    : Array.isArray(profile?.tokens) && profile.tokens.length ? profile.tokens : [];
  const lora = loraForStyleItem(item, profile);
  styleLibraryDetail.innerHTML = `
    <div class="style-detail-preview is-style-asset ${escapeAttribute(item.imageClass)}">
      <img src="${escapeAttribute(item.image)}" alt="${escapeAttribute(item.label)}风格大图预览" />
    </div>
    <div class="style-detail-head">
      <strong>${escapeHtml(item.label)}</strong>
      <span>${escapeHtml(localizeLabel(item.preset))} · ${profile?.vector_dim || 256} dim · ${tokens.length} tokens</span>
    </div>
    <div class="style-detail-param-grid">
      ${controls.map((row) => `
        <div>
          <strong>${escapeHtml(row.label || row.id)}</strong>
          <span>${escapeHtml(localizeLabel(row.value || "未记录"))}</span>
        </div>
      `).join("")}
      <div>
        <strong>风格强度</strong>
        <span>${Number(item.styleWeight).toFixed(2)}</span>
      </div>
      <div>
        <strong>LoRA</strong>
        <span>${escapeHtml(lora.label || item.loraId)} · ${formatWeight(lora.weight ?? item.loraWeight)}</span>
      </div>
    </div>
    <div class="style-token-list style-library-tokens">
      ${tokens.slice(0, 10).map((token) => `<span>${escapeHtml(localizeLabel(token))}</span>`).join("")}
    </div>
    <div class="style-library-prompt">
      <strong>Prompt Token</strong>
      <span>${escapeHtml(item.prompt)}</span>
    </div>
    <button class="generate-button style-library-apply-main" type="button" data-style-apply="${escapeAttribute(item.label)}">应用 ${escapeHtml(item.label)}</button>
  `;
}

async function hydrateStyleLibraryProfile(label) {
  const item = styleCatalogItem(label);
  if (!item || styleLibraryProfiles[item.label] || !apiAvailable) return;
  try {
    const response = await fetch("/api/styles/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(stylePreviewPayloadForItem(item)),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `风格参数加载失败：${response.status}`);
    }
    styleLibraryProfiles[item.label] = payload.style;
    if (!styleLibraryOverlay.hidden && activeStyleLibraryLabel === item.label) {
      renderStyleLibraryDetail(item.label);
    }
  } catch (error) {
    if (!styleLibraryOverlay.hidden && activeStyleLibraryLabel === item.label) {
      apiStatus.textContent = error.message;
    }
  }
}

function stylePreviewPayloadForItem(item) {
  return {
    preset: item.preset,
    prompt: item.prompt,
    lora_id: item.loraId,
    lora_weight: item.loraWeight,
  };
}

function styleCatalogItem(label) {
  const canonicalLabel = canonicalStyleLabel(label);
  return styleCatalog.find((item) => item.label === canonicalLabel) || styleCatalog[0];
}

function styleCatalogControlRows(item) {
  if (Array.isArray(item.controls) && item.controls.length) return item.controls;
  return item.cardParams?.map((param, index) => ({
    id: `param_${index + 1}`,
    label: param.label,
    value: param.value,
  })) || [
    { id: "style", label: "风格", value: item.label },
    { id: "strength", label: "强度", value: Number(item.styleWeight).toFixed(2) },
  ];
}

function loraForStyleItem(item, profile = null) {
  const profileLora = profile?.lora || {};
  const knownLora = loras.find((lora) => lora.id === item.loraId) || fallbackLoras.find((lora) => lora.id === item.loraId) || {};
  return {
    ...knownLora,
    ...profileLora,
    id: profileLora.id || knownLora.id || item.loraId,
    label: profileLora.label || knownLora.label || item.loraId,
    weight: profileLora.weight ?? item.loraWeight,
  };
}

function currentStylePreviewPayload() {
  const label = activeStyleLabel();
  const item = styleCatalogItem(label);
  return stylePreviewPayloadForItem({
    ...item,
    loraId: loraSelect.value || item.loraId,
    loraWeight: Number(loraRange.value || item.loraWeight),
  });
}

function activeStyleLabel() {
  return canonicalStyleLabel(stylePresetGrid.querySelector(".style-swatch.active")?.dataset.style || "写真");
}

function renderStyleAssetPanel(style) {
  const controls = Array.isArray(style?.control_rows) ? style.control_rows : [];
  const tokens = Array.isArray(style?.tokens) ? style.tokens : [];
  const lora = style?.lora || {};
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>${escapeHtml(activeStyleLabel())} Style Model</strong>
        <span>${escapeHtml(localizeLabel(style?.preset || "cinematic"))} · ${style?.vector_dim || 0} dim · ${style?.token_count || tokens.length} tokens</span>
      </div>
      <button class="secondary-button" type="button" data-workspace-action="style-assets">刷新</button>
    </div>
    <div class="style-asset-panel">
      <div class="style-control-grid">
        ${controls.map((row) => styleControlCard(row)).join("")}
      </div>
      <div class="style-token-list">
        ${tokens.map((token) => `<span>${escapeHtml(localizeLabel(token))}</span>`).join("") || "<span>暂无风格 token</span>"}
      </div>
      <div class="style-vector-preview">
        <strong>向量预览</strong>
        <span>${(style?.vector_preview || []).map((value) => Number(value).toFixed(3)).join(" · ") || "未生成"}</span>
      </div>
      <div class="style-lora-row">
        <strong>LoRA</strong>
        <span>${escapeHtml(lora.label || lora.id || "未启用")} · 权重 ${formatWeight(lora.weight)}</span>
      </div>
    </div>
  `;
}

function styleControlCard(row) {
  return `
    <article class="style-control-card">
      <strong>${escapeHtml(row.label || row.id)}</strong>
      <span>${escapeHtml(localizeLabel(row.value || "未记录"))}</span>
    </article>
  `;
}

function normalizeCharacter(character) {
  const preset = character.style?.preset || "cinematic";
  const styleLabels = character.style_labels?.length
    ? character.style_labels.map(localizeLabel)
    : [preset, character.style?.lighting, character.style?.camera_language].filter(Boolean).map(localizeLabel);
  const memoryLabels = character.memory_labels?.length
    ? character.memory_labels.map(localizeLabel)
    : (character.memory?.best_angles || []).map((item) => localizeLabel(item.pose));
  const assetSummary = {
    generation_count: Number(character.asset_summary?.generation_count || 0),
    favorite_count: Number(character.asset_summary?.favorite_count || 0),
    version_count: Number(character.asset_summary?.version_count || character.versions?.length || character.version || 1),
    reference_count: Number(character.asset_summary?.reference_count || character.identity?.reference_count || 0),
    reference_collection_count: Number(character.asset_summary?.reference_collection_count || 0),
    memory_count: Number(character.asset_summary?.memory_count || character.memory_labels?.length || 0),
    last_used_at: character.asset_summary?.last_used_at || character.last_used_at || "",
    updated_at: character.asset_summary?.updated_at || "",
    tags: Array.isArray(character.asset_summary?.tags) ? character.asset_summary.tags : (character.tags || []),
  };
  const referenceAssets = normalizeReferenceAssets(character.reference_assets, character.id);
  const referenceCollections = normalizeReferenceCollections(character.reference_collections);
  const readiness = normalizeIdentityReadiness(character.identity_readiness, referenceAssets);
  return {
    ...character,
    style: { preset, lora: character.style?.lora },
    consistency_percent: character.consistency_percent || Math.round((character.consistency_score || 0) * 100),
    identity_strength: character.identity_strength || 0.8,
    version: character.version || 1,
    style_labels: styleLabels,
    memory_labels: memoryLabels.length ? memoryLabels : ["暂无记忆"],
    prompt: character.prompt || promptInput.value,
    tags: assetSummary.tags,
    asset_summary: assetSummary,
    reference_assets: referenceAssets,
    reference_collections: referenceCollections,
    identity_readiness: readiness,
    memory_entries: normalizeMemoryEntries(character.memory_entries || character.scene_logs),
    last_used_at: assetSummary.last_used_at,
  };
}

function normalizeMemoryEntries(entries) {
  if (!Array.isArray(entries)) return [];
  return entries.map((entry, index) => ({
    id: entry.id || `memory-local-${index + 1}`,
    prompt: entry.prompt || "",
    image: normalizeAssetPath(entry.image || ""),
    pose: entry.pose || "",
    pose_label: entry.pose_label || localizeLabel(entry.pose || "未标注"),
    style: entry.style || "",
    state: entry.state || "",
    success_score: Number(entry.success_score || 0),
    score_percent: Number(entry.score_percent || Math.round(Number(entry.success_score || 0) * 100)),
    generation_id: entry.generation_id || "",
    quality_status: entry.quality_status || "",
    quality_score: entry.quality_score,
    reference_labels: Array.isArray(entry.reference_labels) ? entry.reference_labels : [],
    source: entry.source || "manual",
    created_at: entry.created_at || "",
  }));
}

function normalizeReferenceCollections(collections) {
  const normalized = {};
  referenceCollectionKinds.forEach((kind) => {
    normalized[kind] = normalizeReferenceCollectionItems(kind, collections?.[kind]);
  });
  return normalized;
}

function normalizeReferenceCollectionItems(kind, items) {
  const sourceItems = Array.isArray(items) && items.length ? items : defaultReferenceCollectionItems(kind);
  return sourceItems.map((item, index) => {
    const image = normalizeAssetPath(item.image || item.path || item.source || "");
    const source = normalizeAssetPath(item.source || item.image || item.path || "");
    return {
      id: item.id || `${kind}-${index + 1}`,
      label: item.label || `参考 ${index + 1}`,
      image,
      source,
      visual: item.visual || "",
      alt: item.alt || item.label || "参考图",
      prompt: item.prompt || "",
      active: Boolean(item.active),
      created_at: item.created_at || "",
      updated_at: item.updated_at || "",
    };
  }).slice(0, 20);
}

function defaultReferenceCollectionItems(kind) {
  return (defaultReferenceCollections[kind] || []).map((item) => ({ ...item, active: false }));
}

function normalizeIdentityReadiness(readiness, referenceAssets) {
  if (readiness?.status) {
    return readiness;
  }
  const count = referenceAssets.length;
  return {
    status: count >= 3 ? "ready" : "incomplete",
    label: count >= 3 ? "可训练" : "参考脸不足",
    score: Math.min(1, count / 3),
    reference_count: count,
    duplicate_count: 0,
    can_train: count >= 3,
    checks: [],
  };
}

function normalizeReferenceAssets(referenceAssets, characterId = "character") {
  const sourceAssets = Array.isArray(referenceAssets) && referenceAssets.length
    ? referenceAssets
    : defaultReferenceAssetsForCharacter(characterId);
  const normalized = sourceAssets.map((item, index) => ({
    id: item.id || `${characterId}-face-${index + 1}`,
    label: item.label || ["主图", "侧脸", "回眸", "微笑"][index] || `参考 ${index + 1}`,
    image: normalizeAssetPath(item.image || item.path || item.source || `assets/persona-ref-${(index % 4) + 1}.png`),
    source: normalizeAssetPath(item.source || item.image || item.path || ""),
    prompt: item.prompt || (index === 0 ? "保持参考人脸五官比例和脸型" : "保持同一角色身份"),
    active: Boolean(item.active ?? index === 0),
    created_at: item.created_at || "",
    updated_at: item.updated_at || "",
  })).slice(0, 20);
  if (normalized.length && !normalized.some((item) => item.active)) {
    normalized[0].active = true;
  }
  return normalized;
}

function defaultReferenceAssetsForCharacter(characterId) {
  const offset = { lina: 0, kira: 1, alex: 2 }[characterId] || 0;
  return [0, 1, 2, 3].map((index) => ({
    id: `${characterId}-face-${index + 1}`,
    label: ["主图", "侧脸", "回眸", "微笑"][index],
    image: `assets/persona-ref-${((offset + index) % 4) + 1}.png`,
    prompt: index === 0 ? "保持参考人脸五官比例和脸型" : "保持同一角色身份",
    active: index === 0,
  }));
}

function normalizeAssetPath(path) {
  return String(path || "").replace(/^\.\//, "");
}

function normalizeProject(project) {
  const review = project.review || project.ip_package?.review || {};
  const status = project.status || review.status || "active";
  const ipPackage = project.ip_package || null;
  const releasePackage = project.release_package || ipPackage?.release_package || review.release_package || null;
  return {
    ...project,
    status,
    character_ids: project.character_ids || [],
    characters: project.characters || [],
    channels: project.channels || [],
    deliverables: project.deliverables || [],
    counts: {
      characters: project.counts?.characters || (project.character_ids || []).length,
      generations: project.counts?.generations || 0,
      favorites: project.counts?.favorites || 0,
      deliverables: project.counts?.deliverables || (project.deliverables || []).length,
    },
    review: { ...review, status },
    ip_package: ipPackage,
    release_package: releasePackage,
    asset_counts: project.asset_counts || ipPackage?.asset_counts || {},
    delivery_checklist: project.delivery_checklist || ipPackage?.delivery_checklist || [],
    recommendations: project.recommendations || [],
  };
}

function localizeLabel(label) {
  const normalized = String(label || "").trim();
  const dictionary = {
    "cinematic": "电影感",
    "cinematic portrait": "电影人像",
    "cinematic portrait photography": "电影人像摄影",
    "soft daylight": "柔和日光",
    "soft-daylight": "柔和日光",
    "50mm": "50mm 镜头",
    "50mm portrait lens, shallow depth of field": "50mm 人像镜头 · 浅景深",
    "balanced skin-tone-safe palette": "自然肤色调色",
    "natural high dynamic range light": "自然高动态光线",
    "portrait medium close-up": "人像中近景",
    "portrait": "人像",
    "realistic": "写真",
    "photography": "摄影",
    "skin": "皮肤",
    "tone": "色调",
    "safe": "稳定",
    "natural-bokeh": "自然虚化",
    "warm-skin": "暖调肤色",
    "consistent character portrait": "一致性角色肖像",
    "commercial": "商业大片",
    "luxury-product": "奢华产品",
    "golden-light": "金色高光",
    "glass-reflection": "玻璃反射",
    "premium-skincare": "高端护肤",
    "brand-campaign": "品牌广告",
    "product-poster": "产品海报",
    "hero-packshot": "主视觉产品",
    "golden-campaign": "金色广告",
    "glossy-reflection": "镜面反射",
    "premium-layout": "高级版式",
    "controlled studio key light": "棚拍主光",
    "campaign-ready medium shot": "广告中景",
    "polished brand campaign portrait": "品牌广告人像",
    "anime": "动漫",
    "clean illustrated character render": "干净插画角色",
    "clean saturated palette": "干净高饱和配色",
    "anime-face": "动漫脸型",
    "clean-line": "干净线条",
    "soft-glow": "柔和辉光",
    "cel": "赛璐璐",
    "illustrated": "插画",
    "soft-texture": "柔和纹理",
    "editorial": "编辑感",
    "poster": "海报",
    "brush-texture": "笔触纹理",
    "paper-grain": "纸张颗粒",
    "editorial-color": "编辑色彩",
    "3d-render": "3D",
    "studio-polish": "棚拍精修",
    "subsurface": "次表面材质",
    "material-safe": "材质稳定",
    "material-polish": "材质高光",
    "studio-render": "棚拍渲染",
    "moody": "低照度",
    "drama-light": "剧照布光",
    "campaign-light": "广告布光",
    "cinematic-still": "电影剧照",
    "moody-practical": "实景暗光",
    "contrast-grade": "对比调色",
    "oriental-palette": "东方色彩",
    "elegant-fabric": "典雅织物",
    "ink-wash": "水墨",
    "silk-texture": "绢面纹理",
    "healing": "治愈",
    "warm-palette": "暖色调",
    "gentle": "温柔",
    "gentle-daylight": "柔和日光",
    "pastel-air": "粉彩空气感",
    "soft-life": "生活感",
    "coffee shop morning": "清晨咖啡馆",
    "rainy night street": "雨夜街道",
    "studio headshot": "棚拍头像",
    "walking in morning light": "清晨光线中行走",
    "school rooftop": "学校天台",
    "city neon": "城市霓虹",
    "spring garden": "春日花园",
    "studio campaign": "棚拍广告",
    "product launch": "产品发布",
    "outdoor billboard": "户外海报",
    "front": "正面",
    "three-quarter": "四分之三侧脸",
    "side": "侧脸",
    "reference_pose": "参考姿态",
    "text-to-image": "文生图",
    "image-to-image": "图生图",
    "inpaint": "局部重绘",
  };
  return dictionary[normalized] || normalized.replaceAll("identity locked", "身份锁定");
}

function renderGenerationGrid() {
  const visibleGenerations = sortedGenerations();

  if (!visibleGenerations.length) {
    outputGrid.replaceChildren(emptyTile());
    return;
  }

  outputGrid.replaceChildren(...visibleGenerations.slice(0, 12).map((generation, index) => generationTile(generation, index)));
}

function generationTile(generation, index) {
  const article = document.createElement("article");
  const isNewGeneration = latestGenerationIds.has(generation.id);
  article.className = [
    "image-tile",
    isNewGeneration ? "is-new" : "",
  ].filter(Boolean).join(" ");
  article.dataset.id = generation.id;
  article.style.setProperty("--generation-aspect-ratio", aspectRatioForSize(generation.size));
  article.tabIndex = 0;
  article.setAttribute("role", "group");
  const displayName = generationDisplayName(generation);
  article.setAttribute("aria-label", `${displayName} 生成缩略图，点击打开大图详情`);

  const image = document.createElement("img");
  image.src = imageForGeneration(generation, index);
  image.alt = `${displayName} 生成图 ${generation.variant || index + 1}`;

  const meta = document.createElement("div");
  meta.className = "tile-meta";
  meta.textContent = [
    displayName,
    isCharacterSubject(generation) ? `v${generation.character_version || 1}` : "按提示词",
    localizeLabel(generation.mode),
    shortModelRouteLabel(generation.model_route),
    isCharacterSubject(generation) ? generation.lora_name || labelForLora(generation.lora_id) : "",
    labelForDrift(generation.drift_risk),
  ].filter(Boolean).join(" · ");

  const quality = qualityForGeneration(generation);
  const qualityBadge = document.createElement("div");
  qualityBadge.className = `quality-badge ${qualityClass(quality.status)}`.trim();
  qualityBadge.textContent = `${qualityLabel(quality.status)} ${qualityPercent(generation)}%`;

  const newBadge = document.createElement("div");
  newBadge.className = "new-generation-badge";
  newBadge.textContent = "刚刚生成";

  const actions = document.createElement("div");
  actions.className = "tile-actions";
  actions.append(
    actionButton("download", "下载"),
    actionButton("favorite", generation.favorite ? "已收藏" : "收藏"),
    actionButton("reuse", "复用"),
    actionButton("lock", "锁脸+"),
    actionButton("remix", "变体"),
    actionButton("delete", "删除"),
  );

  article.append(image, meta, qualityBadge);
  if (isNewGeneration) {
    article.append(newBadge);
  }
  article.append(actions);
  return article;
}

function generationDisplayName(generation) {
  const subject = generation?.subject_hint || "portrait";
  const labels = {
    male: "男性主体",
    child: "儿童主体",
    car: "汽车主体",
    product: "产品主体",
    landscape: "风景主体",
    animal: "动物主体",
  };
  return labels[subject] || generation?.character_name || generation?.character_id || "角色";
}

function isCharacterSubject(generation) {
  return !generation?.subject_hint || ["portrait", "female"].includes(generation.subject_hint);
}

function emptyTile() {
  const article = document.createElement("article");
  article.className = "image-tile empty-tile";
  article.textContent = "暂无生成图";
  return article;
}

function generationPlaceholderTile(index, total) {
  const article = document.createElement("article");
  const size = getCheckedValue("size");
  article.className = "image-tile generation-placeholder";
  article.style.setProperty("--generation-aspect-ratio", aspectRatioForSize(size));
  article.setAttribute("role", "status");
  article.setAttribute("aria-live", "polite");
  article.setAttribute("aria-label", `第 ${index + 1} 张图片正在生成`);

  const frame = document.createElement("div");
  frame.className = "generation-placeholder-frame";
  const pulse = document.createElement("span");
  pulse.className = "generation-placeholder-pulse";
  const title = document.createElement("strong");
  title.textContent = "正在生成...";
  const meta = document.createElement("span");
  meta.textContent = `${selectedImageModelLabel()} · ${size} · ${index + 1}/${total}`;
  frame.append(pulse, title, meta);
  article.append(frame);
  return article;
}

function actionButton(action, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.action = action;
  button.textContent = label;
  return button;
}

function renderMemoryInsights(character) {
  const insights = character.memory_insights || {};
  const bestAngles = insights.best_angles || [];
  const preferredStyles = insights.preferred_styles || [];
  const failureAdvice = insights.failure_advice || {};
  const blockedStyles = failureAdvice.blocked_styles || [];
  const average = Number(insights.average_success_score || 0);

  const angleMarkup = bestAngles.length
    ? bestAngles.slice(0, 2).map((item) => `
      <button class="memory-card" type="button" data-memory-prompt="${localizeLabel(item.pose)} 构图，身份锁定">
        <strong>${localizeLabel(item.pose)}</strong>
        <span>成功率 ${Math.round(Number(item.average_score || 0) * 100)}% · ${item.uses || 1} 次</span>
      </button>
    `).join("")
    : `<span class="memory-card muted-card">暂无角度数据</span>`;

  const styleMarkup = preferredStyles.length
    ? preferredStyles.slice(0, 2).map((item) => `
      <button class="memory-card" type="button" data-memory-style="${localizeLabel(item.style)}">
        <strong>${localizeLabel(item.style)}</strong>
        <span>偏好 ${Math.round(Number(item.average_score || 0) * 100)}%</span>
      </button>
    `).join("")
    : `<span class="memory-card muted-card">暂无偏好风格</span>`;

  const failureMarkup = blockedStyles.length
    ? `<span class="memory-warning">避开：${blockedStyles.map(localizeLabel).join("、")}</span>`
    : `<span class="memory-ok">避坑：暂无失败风格</span>`;

  memoryInsights.innerHTML = `
    <div class="memory-head">
      <strong>记忆推荐</strong>
      <span>平均成功率 ${Math.round(average * 100)}%</span>
    </div>
    <div class="memory-card-grid">${angleMarkup}${styleMarkup}</div>
    ${failureMarkup}
    <div class="memory-actions">
      <button class="secondary-button" type="button" data-memory-action="manage">管理记忆</button>
      <span>${character.memory_entries?.length || 0} 条近期资产</span>
    </div>
  `;
}

async function showMemoryStorePanel(characterId = activeCharacterId) {
  const character = characters.find((item) => item.id === characterId) || characters[0];
  showWorkspaceSurface("记忆资产");

  if (!apiAvailable) {
    renderMemoryStorePanel(character, character.memory_entries || [], character.memory_insights || {});
    apiStatus.textContent = "本地预览记忆资产";
    return;
  }

  try {
    const response = await fetch(`/api/characters/${characterId}/memory`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const entries = normalizeMemoryEntries(payload.entries || []);
    const updatedCharacter = normalizeCharacter({
      ...character,
      memory_entries: entries.slice(0, 4),
      memory_insights: payload.insights || character.memory_insights,
      asset_summary: {
        ...(character.asset_summary || {}),
        memory_count: entries.length,
      },
    });
    characters = characters.map((item) => (item.id === characterId ? updatedCharacter : item));
    renderMemoryStorePanel(updatedCharacter, entries, payload.insights || updatedCharacter.memory_insights || {});
    apiStatus.textContent = `${updatedCharacter.name} 记忆资产已加载`;
  } catch (error) {
    renderMemoryStorePanel(character, character.memory_entries || [], character.memory_insights || {});
    apiStatus.textContent = error.message;
  }
}

function renderMemoryStorePanel(character, entries, insights) {
  activeMemoryEntries = entries;
  const average = Math.round(Number(insights.average_success_score || 0) * 100);
  const failedCount = entries.filter((entry) => entry.quality_status === "fail" || entry.success_score <= 0.45).length;
  const rows = entries.length
    ? entries.map((entry) => memoryEntryCard(entry)).join("")
    : `<div class="memory-entry-card empty-memory">暂无可管理记忆</div>`;
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>${escapeHtml(character?.name || "角色")} Memory Store</strong>
        <span>${entries.length} 条场景记忆 · 平均 ${average}% · 失败 ${failedCount}</span>
      </div>
      <button class="secondary-button" type="button" data-workspace-action="manage-memory">刷新</button>
    </div>
    <div class="memory-entry-list">
      ${rows}
    </div>
  `;
}

function memoryEntryCard(entry) {
  const generationButton = entry.generation_id
    ? `<button class="secondary-button" type="button" data-open-generation-id="${escapeAttribute(entry.generation_id)}">打开生成图</button>`
    : "";
  const references = entry.reference_labels.length
    ? `<span>参考：${entry.reference_labels.slice(0, 3).map(escapeHtml).join("、")}</span>`
    : "";
  return `
    <article class="memory-entry-card">
      <img src="${escapeAttribute(entry.image || "assets/lina-morning.svg")}" alt="${escapeAttribute(entry.pose_label || "记忆图")}">
      <div>
        <strong>${escapeHtml(entry.prompt || "未命名场景")}</strong>
        <span>${escapeHtml(entry.pose_label || "未标注")} · ${escapeHtml(localizeLabel(entry.style) || "未标注风格")} · 成功率 ${entry.score_percent}%</span>
        <span>${escapeHtml(memoryQualityLabel(entry.quality_status))} · ${entry.source === "generation" ? "生成写入" : "手动记录"}</span>
        ${references}
      </div>
      <div class="memory-entry-actions">
        <button class="secondary-button" type="button" data-memory-entry-id="${escapeAttribute(entry.id)}">复用</button>
        ${generationButton}
        <button class="secondary-button danger-button" type="button" data-delete-memory-id="${escapeAttribute(entry.id)}">删除</button>
      </div>
    </article>
  `;
}

function memoryQualityLabel(status) {
  return {
    pass: "质检通过",
    review: "需要复核",
    fail: "失败记忆",
  }[status] || "记忆记录";
}

async function deleteMemoryEntry(memoryId) {
  if (!apiAvailable) {
    const character = characters.find((item) => item.id === activeCharacterId);
    if (character) {
      character.memory_entries = (character.memory_entries || []).filter((entry) => entry.id !== memoryId);
      renderMemoryStorePanel(character, character.memory_entries, character.memory_insights || {});
    }
    apiStatus.textContent = "本地记忆已移除";
    return;
  }

  try {
    const response = await fetch(`/api/characters/${activeCharacterId}/memory/${memoryId}`, { method: "DELETE" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `删除失败：${response.status}`);
    }
    const updatedCharacter = normalizeCharacter(payload.character);
    const currentPrompt = promptInput.value;
    const currentNegativePrompt = negativePromptInput.value;
    characters = characters.map((item) => (item.id === activeCharacterId ? updatedCharacter : item));
    setCharacter(activeCharacterId);
    promptInput.value = currentPrompt;
    negativePromptInput.value = currentNegativePrompt;
    updatePromptCounters();
    renderMemoryStorePanel(updatedCharacter, normalizeMemoryEntries(payload.entries || []), payload.insights || updatedCharacter.memory_insights || {});
    apiStatus.textContent = "记忆已删除，偏好已重算";
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

function openGenerationDetail(generation) {
  if (canvasEditState.open && canvasEditState.generationId !== generation.id) {
    closeCanvasEditPanel();
  }
  selectedGenerationId = generation.id;
  const quality = qualityForGeneration(generation);
  const displayName = generationDisplayName(generation);
  const mediaFrame = detailImage.closest(".image-detail-media");
  mediaFrame?.style.setProperty("--generation-aspect-ratio", aspectRatioForSize(generation.size));
  detailImage.src = imageForGeneration(generation, generation.variant || 1);
  detailImage.alt = `${displayName} 生成图详情`;
  detailMeta.textContent = [
    displayName,
    generation.size || "",
    isCharacterSubject(generation) ? `v${generation.character_version || 1}` : "按提示词主体",
    localizeLabel(generation.mode),
    labelForDrift(generation.drift_risk),
  ].filter(Boolean).join(" · ");
  detailPrompt.textContent = generation.prompt || "未记录";
  detailNegativePrompt.textContent = generation.negative_prompt || "未记录";
  detailConsistency.textContent = isCharacterSubject(generation)
    ? `身份 ${Number(generation.identity_weight || 0).toFixed(2)} · 风格 ${Number(generation.style_weight || 0).toFixed(2)} · 差值 ${Number(quality.identity_margin || 0).toFixed(2)}`
    : "非人像主体 · 不启用角色脸一致性";
  detailQuality.textContent = [
    `${qualityLabel(quality.status)} · ${qualityScoreLabel(quality)} ${qualityPercent(generation)}%`,
    `阈值 ${Math.round(Number(quality.threshold || 0.82) * 100)}%`,
    identitySimilarityLabel(quality.identity_similarity),
    quality.review_note || "本地一致性质检",
  ].filter(Boolean).join(" · ");
  detailModelRoute.textContent = labelForModelRoute(generation.model_route);
  detailJob.textContent = generation.job_id || "旧记录未绑定任务";
  detailReferenceGuidance.textContent = labelForReferenceGuidance(generation.reference_guidance);
  detailConditioning.textContent = labelForConditioningManifest(generation.conditioning_manifest);
  detailLora.textContent = isCharacterSubject(generation)
    ? `${generation.lora_name || labelForLora(generation.lora_id) || "未启用"} · ${Number(generation.lora_weight || 0).toFixed(2)}`
    : "非人像主体不启用身份 LoRA";
  syncDetailActionState(generation);
  imageDetailOverlay.hidden = false;
  closeImageDetail.focus();
  apiStatus.textContent = "已打开生成图详情";
}

function closeGenerationDetail() {
  closeCanvasEditPanel();
  imageDetailOverlay.hidden = true;
  selectedGenerationId = "";
}

function posteriorFaceScore(generation) {
  const identity = Number(generation.identity_weight || 0.7);
  const style = Number(generation.style_weight || 0.6);
  const margin = Math.max(0, identity - style);
  return Math.round(Math.min(0.98, 0.72 + margin * 0.8) * 100);
}

function qualityForGeneration(generation) {
  if (generation?.quality?.face_match_score !== undefined) {
    return generation.quality;
  }
  const score = posteriorFaceScore(generation) / 100;
  const threshold = 0.82;
  return {
    face_match_score: score,
    threshold,
    match: score >= threshold,
    status: score >= threshold ? "pass" : "review",
    identity_margin: Number(generation?.identity_weight || 0.7) - Number(generation?.style_weight || 0.6),
    review_note: "旧记录已按本地权重回填质检分。",
  };
}

function qualityPercent(generation) {
  return Math.round(Number(qualityForGeneration(generation).face_match_score || 0) * 100);
}

function qualityScoreLabel(quality) {
  if (quality?.score_kind === "identity_unverified_proxy") return "未认证代理分";
  if (quality?.score_kind === "conditioning_proxy") return "条件代理分";
  if (quality?.score_kind === "subject_gate") return "主体通过";
  return "匹配";
}

function identitySimilarityLabel(similarity) {
  if (!similarity) return "真实同人验证未接入";
  if (similarity.status === "skipped") return "非人像跳过同人验证";
  if (similarity.status === "structure_proxy_pass") return "脸部结构代理通过 · 非同人认证";
  if (similarity.status === "heuristic_pass") return "OpenCV 脸检通过 · 非同人认证";
  if (similarity.status === "review") return "脸型需人工复核";
  if (similarity.status === "not_available") return "真实同人验证未接入";
  return "真实同人验证未接入";
}

function qualityLabel(status) {
  if (status === "pass") return "通过";
  if (status === "review") return "复核";
  if (status === "fail") return "未过";
  return "质检";
}

function qualityClass(status) {
  if (status === "pass") return "pass";
  if (status === "fail") return "fail";
  return "review";
}

function qualitySummary(items) {
  if (!items.length) return "质检暂无";
  const passed = items.filter((item) => qualityForGeneration(item).status === "pass").length;
  const lowest = Math.min(...items.map((item) => qualityPercent(item)));
  return `质检通过 ${passed}/${items.length} · 最低 ${lowest}%`;
}

function aspectRatioForSize(size) {
  return {
    "1:1": "1 / 1",
    "3:4": "3 / 4",
    "4:3": "4 / 3",
    "16:9": "16 / 9",
    "9:16": "9 / 16",
  }[size] || "3 / 4";
}

function ratioNumberForSize(size) {
  const [width, height] = String(size || "3:4").split(":").map(Number);
  if (!width || !height) return 3 / 4;
  return width / height;
}

function selectedImageModelLabel() {
  return modelSelect.options[modelSelect.selectedIndex]?.textContent?.trim() || modelSelect.value;
}

function providerHasRealGenerationRoute(provider) {
  return ["wanx", "volcengine", "kling", "fal", "flux"].includes(provider);
}

function shortModelRouteLabel(route) {
  if (!route) return "本地演示";
  if (route.mode === "external_api") {
    if (route.real_generation) {
      const kindLabel = route.generation_kind === "img2img" ? "图生图" : "文生图";
      return route.provider_label ? `真实API:${route.provider_label}·${kindLabel}` : `真实 API·${kindLabel}`;
    }
    if (providerHasRealGenerationRoute(route.provider)) {
      return route.provider_label ? `本地预览:${route.provider_label}` : "本地预览";
    }
    return route.provider_label ? `未接入API:${route.provider_label}` : "API未接入";
  }
  return route.label ? "本地预览" : "本地演示";
}

function labelForModelRoute(route) {
  if (!route) return "本地演示模型";
  const label = route.label || route.model || "未记录";
  if (route.mode === "external_api") {
    const base = route.base_url ? ` · ${route.base_url}` : "";
    const kindLabel = route.generation_kind === "img2img" ? "图生图" : route.generation_kind === "t2i" ? "文生图" : "";
    const kindSuffix = kindLabel ? ` · ${kindLabel}` : "";
    const prefix = route.real_generation
      ? "真实 API"
      : providerHasRealGenerationRoute(route.provider)
        ? "本地预览"
        : "API 已配置但本地未接入真实生成";
    return `${prefix} · ${label}${kindSuffix}${base}`;
  }
  return `本地演示 · ${label}`;
}

function labelForReferenceGuidance(guidance) {
  const groups = Array.isArray(guidance) ? guidance : [];
  const labels = groups.flatMap((group) => {
    const groupLabel = group.label || referenceCategories[group.kind]?.label || "参考";
    return (group.items || []).map((item) => `${groupLabel}:${item.label}`);
  });
  return labels.length ? labels.join(" · ") : "未使用额外参考";
}

function labelForConditioningManifest(manifest) {
  if (!manifest) return "旧记录未保存条件包";
  const references = Array.isArray(manifest.references)
    ? manifest.references.reduce((total, group) => total + (group.items || []).length, 0)
    : Number(manifest.reference_count || 0);
  const memory = manifest.memory || {};
  const controlnet = manifest.controlnet || {};
  const promptLength = String(manifest.provider_prompt || "").length;
  return [
    manifest.uses_identity_lock ? "身份锁定已编译" : "按提示词主体",
    controlnet.enabled ? `姿态:${controlnet.pose_label || poseControlLabel(controlnet.pose)}` : "",
    references ? `参考 ${references}` : "无额外参考",
    memory.best_angle ? `记忆:${localizeLabel(memory.best_angle)}` : "",
    manifest.prompt_hash ? `Prompt ${promptLength}字 · ${manifest.prompt_hash}` : "",
  ].filter(Boolean).join(" · ");
}

function sortedGenerations() {
  const showAllCharacters = workspaceTitle.textContent === "我的作品";
  const scopedGenerations = showAllCharacters
    ? generations
    : generations.filter((generation) => generation.character_id === activeCharacterId);
  const visibleGenerations = favoritesOnly.checked
    ? scopedGenerations.filter((generation) => generation.favorite)
    : [...scopedGenerations];

  if (sortSelect.value === "一致性最高") {
    return [...visibleGenerations].sort((left, right) => qualityPercent(right) - qualityPercent(left));
  }

  if (sortSelect.value === "收藏优先") {
    return [...visibleGenerations].sort((left, right) => Number(right.favorite) - Number(left.favorite));
  }

  return visibleGenerations;
}

function updatePromptCounters() {
  promptCount.textContent = String(promptInput.value.length);
  negativeCount.textContent = String(negativePromptInput.value.length);
}

function updateGenerateSummary() {
  const count = Number(getCheckedValue("count") || 4);
  const costPerImage = Number(accountState.cost_per_image || 2);
  generateButton.textContent = `生成 (${count})`;
  costLine.textContent = `消耗 ${count * costPerImage}`;
}

function setWorkspaceMode(mode, options = {}) {
  hideAccountCenter();

  if (mode === "首页") {
    workspaceTitle.textContent = "生成结果";
    showResultSurface();
    renderGenerationGrid();
    apiStatus.textContent = "首页生成工作区";
    return;
  }

  workspaceTitle.textContent = mode;

  if (mode === "我的作品") {
    showResultSurface({ keepWorkspacePanel: true, hideNotice: true });
    renderWorksPanel();
    renderGenerationGrid();
    apiStatus.textContent = "我的作品已打开";
    return;
  }

  showWorkspaceSurface(mode);

  if (mode === "探索") {
    renderExplorePanel();
    apiStatus.textContent = "探索面板已打开";
    return;
  }

  if (mode === "项目") {
    renderProjectsPanel();
    apiStatus.textContent = "项目已打开";
    return;
  }

  if (mode === "模型广场") {
    renderModelPlazaPanel(options);
    apiStatus.textContent = options.showPlans ? "升级与模型广场已打开" : "模型广场已打开";
  }
}

function setGenerationMode(mode) {
  activeGenerationMode = mode;
  modeContextPanel.hidden = false;

  if (mode === "文生图") {
    renderGenerationModePanel({
      cards: [
        {
          title: "身份锁定",
          text: "身份权重高于风格",
          prompt: "身份锁定，高一致性面部结构，稳定五官",
          style: "写真",
        },
        {
          title: "轻写真",
          text: "自然光和浅景深",
          prompt: "清晨自然光，轻写真，人像中近景，50mm 镜头，身份锁定",
          style: "摄影",
        },
        {
          title: "商业",
          text: "棚拍主光和品牌质感",
          prompt: "商业广告，产品级棚拍主光，金色高光，玻璃反射，品牌大片质感",
          style: "商业广告",
        },
      ],
    });
  }

  if (mode === "图生图") {
    ensureReferenceEnabled();
    renderGenerationModePanel({
      cards: [
        { title: "参考图", text: "选择图片加入参考栏", action: "upload-reference" },
        { title: "加强约束", text: "身份权重提升到 0.90+", action: "strengthen-reference" },
        {
          title: "构图保持",
          text: "沿用参考图姿态和光线",
          prompt: "沿用参考图构图，保持人物姿态和光线方向，身份锁定",
          style: "写真",
        },
      ],
    });
  }

  if (mode === "局部重绘") {
    renderGenerationModePanel({
      cards: [
        { title: "重绘面部", text: "保持身份，只修复面部区域", action: "mask-face" },
        { title: "保护背景", text: "避免背景被重绘破坏", action: "mask-background" },
        {
          title: "修复细节",
          text: "清理噪点、手指和五官错位",
          prompt: "局部修复细节，清理噪点，保持五官稳定，身份锁定",
          style: "写真",
        },
      ],
    });
  }

  apiStatus.textContent = `${mode} 已就绪`;
}

function renderGenerationModePanel(config) {
  modeContextPanel.innerHTML = `
    <div class="quick-card-grid compact-mode-grid">
      ${config.cards.map((item) => {
        const actionAttr = item.action ? `data-workspace-action="${item.action}"` : "";
        const promptAttr = item.prompt ? `data-prompt="${item.prompt}"` : "";
        const styleAttr = item.style ? `data-style="${item.style}"` : "";
        return `
          <button class="quick-card" type="button" ${actionAttr} ${promptAttr} ${styleAttr}>
            <strong>${item.title}</strong>
            <span>${item.text}</span>
          </button>
        `;
      }).join("")}
    </div>
  `;
}

function renderExplorePanel() {
  const prompts = [
    {
      title: "清晨公园写真",
      style: "写真",
      prompt: "一个年轻的亚洲女性，清晨公园，自然日光，发丝被微风吹动，写真质感，50mm 镜头，浅景深，身份锁定",
    },
    {
      title: "雨夜街道电影感",
      style: "美剧",
      prompt: "雨夜街道，角色回头看向镜头，湿润反光路面，电影感蓝绿色调，三分之二侧脸，身份锁定",
    },
    {
      title: "品牌棚拍头像",
      style: "商业广告",
      prompt: "商业广告头像，干净摄影棚，产品级主光，清晰面部结构，品牌大片质感，身份锁定",
    },
    {
      title: "高端产品海报",
      style: "商业海报",
      prompt: "高端护肤品商业海报，中心产品主视觉，金色高光，花瓣和反射质感，品牌发布画面",
    },
  ];
  workspaceModePanel.innerHTML = `
    <div class="quick-card-grid">
      ${prompts.map((item) => `
        <button class="quick-card" type="button" data-style="${item.style}" data-prompt="${item.prompt}">
          <strong>${item.title}</strong>
          <span>${item.style}</span>
        </button>
      `).join("")}
    </div>
  `;
}

function projectAssetCounts(project) {
  const counts = project?.ip_package?.asset_counts || project?.asset_counts || {};
  return {
    characters: counts.characters ?? project?.counts?.characters ?? 0,
    identity_references: counts.identity_references ?? 0,
    non_face_references: counts.non_face_references ?? 0,
    active_non_face_references: counts.active_non_face_references ?? 0,
    generated_images: counts.generated_images ?? project?.counts?.generations ?? 0,
    favorite_images: counts.favorite_images ?? project?.counts?.favorites ?? 0,
    quality_passed_images: counts.quality_passed_images ?? 0,
    memory_logs: counts.memory_logs ?? 0,
    versions: counts.versions ?? 0,
    generation_jobs: counts.generation_jobs ?? 0,
    deliverables: counts.deliverables ?? project?.counts?.deliverables ?? 0,
  };
}

function projectDeliveryChecklist(project) {
  return project?.ip_package?.delivery_checklist || project?.delivery_checklist || [];
}

function projectPackageCompleteness(project) {
  const checklist = projectDeliveryChecklist(project);
  if (!checklist.length) return "未生成";
  const passed = checklist.filter((check) => check.status === "passed").length;
  return `${passed}/${checklist.length} 项`;
}

function projectReleasePackage(project) {
  return project?.release_package || project?.ip_package?.release_package || project?.review?.release_package || null;
}

function projectReleaseLabel(project) {
  const release = projectReleasePackage(project);
  const status = release?.status || "not_built";
  const labels = {
    ready: "发布包 ready",
    needs_review: "发布包需复核",
    not_built: "未构建发布包",
    withdrawn: "发布包已撤回",
  };
  return labels[status] || localizeLabel(status);
}

function projectCharacters(project) {
  return project?.characters?.length
    ? project.characters
    : (project?.character_ids || []).map((id) => characters.find((character) => character.id === id)).filter(Boolean);
}

function projectCoverImage(project) {
  const projectCharacterIds = new Set([
    ...(project?.character_ids || []),
    ...(project?.characters || []).map((character) => character.id).filter(Boolean),
  ]);
  const latestGeneration = [...generations]
    .filter((generation) => (
      generation.project_id === project?.id
      || projectCharacterIds.has(generation.character_id)
    ))
    .sort((left, right) => new Date(right.created_at || 0) - new Date(left.created_at || 0))[0];
  if (latestGeneration) {
    return imageForGeneration(latestGeneration);
  }
  const character = projectCharacters(project)[0];
  const references = normalizeReferenceAssets(character?.reference_assets, character?.id || "character");
  return (references.find((item) => item.active) || references[0])?.image || "assets/persona-ref-1.png";
}

function renderProjectsPanel() {
  const activeProject = projects.find((project) => project.id === activeProjectId) || projects[0];
  activeProjectId = activeProject?.id || activeProjectId;
  const projectCards = projects.map((project) => {
    const cover = projectCoverImage(project);
    return `
      <div class="quick-card project-card${project.id === activeProjectId ? " active" : ""}">
        <button class="project-select" type="button" data-project-id="${project.id}">
          <span class="project-cover">
            <span class="project-cover-backdrop" aria-hidden="true">
              <img src="${escapeAttribute(cover)}" alt="" loading="lazy" />
            </span>
            <img class="project-cover-image" src="${escapeAttribute(cover)}" alt="${escapeAttribute(`${project.name} 项目封面`)}" loading="lazy" />
            <span class="project-cover-label">${projectStatusLabel(project.status)}</span>
          </span>
          <span class="project-select-body">
            <strong>${project.name}</strong>
            <span>${project.user_segment} · ${project.level}</span>
            <span>${project.counts.characters} 角色 · ${project.counts.generations} 图 · ${project.counts.favorites} 收藏</span>
          </span>
        </button>
        <button class="project-delete" type="button" data-delete-project-id="${project.id}" aria-label="删除项目 ${project.name}">×</button>
      </div>
    `;
  }).join("");
  const activeCharacters = projectCharacterNames(activeProject).join("、") || "未绑定角色";
  const deliverables = (activeProject?.deliverables || []).map((item) => `<span>${item}</span>`).join("");
  const recommendations = (activeProject?.recommendations || []).map((item) => `<span>${item}</span>`).join("");
  const review = activeProject?.review || {};
  const reviewLabel = review.label || projectStatusLabel(activeProject?.status);
  const licenseLabel = projectLicenseLabel(activeProject);
  const releasePackage = projectReleasePackage(activeProject);
  const releaseLabel = projectReleaseLabel(activeProject);
  const releaseArtifact = releasePackage?.artifact_path ? compactPath(releasePackage.artifact_path) : "未归档";
  const releaseBuiltAt = releasePackage?.built_at ? `构建：${compactDateTime(releasePackage.built_at)}` : "未构建";
  const assetCounts = projectAssetCounts(activeProject);
  const packageCompleteness = projectPackageCompleteness(activeProject);
  const reviewTime = review.approved_at
    ? `批准：${compactDateTime(review.approved_at)}`
    : review.submitted_at
      ? `提交：${compactDateTime(review.submitted_at)}`
      : "未提交审阅";
  workspaceModePanel.innerHTML = `
    <div class="quick-card-grid project-grid">
      ${projectCards}
    </div>
    <div class="project-detail-band">
      <div>
        <strong>${activeProject?.name || "暂无项目"}</strong>
        <span>${activeProject?.goal || "创建项目后沉淀角色资产"}</span>
      </div>
      <div class="project-meta-grid">
        <span>用户模型：${activeProject?.user_segment || "创作者"}</span>
        <span>产品层级：${activeProject?.level || "Level 3 Character OS"}</span>
        <span>绑定角色：${activeCharacters}</span>
        <span>状态：${projectStatusLabel(activeProject?.status)}</span>
      </div>
      <div class="project-review-row">
        <span>审阅：${reviewLabel}</span>
        <span>授权：${licenseLabel}</span>
        <span>${reviewTime}</span>
      </div>
      <div class="project-release-row">
        <span>发布包：${releaseLabel}</span>
        <span>${releaseBuiltAt}</span>
        <span>归档：${releaseArtifact}</span>
      </div>
      <div class="project-asset-row">
        <span>资产包：${assetCounts.characters} 角色 · ${assetCounts.generated_images} 图 · ${assetCounts.favorite_images} 收藏</span>
        <span>参考：${assetCounts.identity_references} 人脸 · ${assetCounts.non_face_references} 非人脸</span>
        <span>质检：${assetCounts.quality_passed_images}/${assetCounts.generated_images} · 清单 ${packageCompleteness}</span>
      </div>
      <div class="project-review-actions">
        <button class="secondary-button" type="button" data-workspace-action="submit-project-review">提交审阅</button>
        <button class="secondary-button" type="button" data-workspace-action="approve-project">批准发布</button>
        <button class="secondary-button" type="button" data-workspace-action="build-release-package">构建发布包</button>
        <button class="secondary-button" type="button" data-workspace-action="withdraw-project-review">撤回草稿</button>
      </div>
      <div class="project-chip-row">${deliverables}</div>
      <div class="project-chip-row muted">${recommendations}</div>
    </div>
    <div class="quick-card-grid project-action-grid">
      <button class="quick-card" type="button" data-workspace-action="create-project">
        <strong>新建项目</strong>
        <span>用当前角色创建一个创作者/商业项目</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="bind-project-character">
        <strong>绑定当前角色</strong>
        <span>把 ${characterName.textContent} 加入当前项目资产</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="export-ip-pack">
        <strong>导出 IP 包</strong>
        <span>下载身份、风格、记忆和商业交付摘要</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="build-release-package">
        <strong>商业发布包</strong>
        <span>训练身份包、检查部署和归档 release artifact</span>
      </button>
    </div>
  `;
}

async function selectProject(projectId) {
  activeProjectId = projectId;
  setActiveNavByName("项目");
  showWorkspaceSurface("项目");
  if (apiAvailable) {
    try {
      const response = await fetch(`/api/projects/${projectId}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || `API ${response.status}`);
      }
      projects = projects.map((project) => (project.id === projectId ? normalizeProject(payload.project) : project));
    } catch (error) {
      apiStatus.textContent = error.message;
    }
  }
  renderProjectsPanel();
  const project = projects.find((item) => item.id === projectId);
  apiStatus.textContent = project ? `已选中项目：${project.name}` : "项目已切换";
}

async function deleteProject(projectId) {
  const project = projects.find((item) => item.id === projectId);
  if (!project) return;

  if (!apiAvailable) {
    projects = projects.filter((item) => item.id !== projectId);
    if (activeProjectId === projectId) {
      activeProjectId = projects[0]?.id || "";
    }
    renderProjectsPanel();
    apiStatus.textContent = `${project.name} 已删除`;
    return;
  }

  try {
    const response = await fetch(`/api/projects/${projectId}`, { method: "DELETE" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `删除失败：${response.status}`);
    }
    projects = (payload.projects || []).map(normalizeProject);
    if (activeProjectId === projectId || !projects.some((item) => item.id === activeProjectId)) {
      activeProjectId = projects[0]?.id || "";
    }
    renderProjectsPanel();
    apiStatus.textContent = `${payload.deleted?.name || project.name} 已删除`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function createProjectFromCurrent() {
  const character = characters.find((item) => item.id === activeCharacterId);
  const segment = activePlanId === "upgrade-business" ? "商业用户" : "创作者";
  const body = {
    name: `${character?.name || "角色"} 系列项目`,
    user_segment: segment,
    level: segment === "商业用户" ? "Level 4 Visual IP System" : "Level 3 Character OS",
    character_id: activeCharacterId,
    goal: segment === "商业用户" ? "沉淀长期可复用商业 IP 资产" : "持续生成同一角色的系列内容",
    channels: segment === "商业用户" ? ["广告投放", "电商主图", "品牌海报"] : ["小红书", "抖音", "短剧分镜"],
    deliverables: segment === "商业用户" ? ["IP 资产包", "商业授权摘要", "品牌 LoRA"] : ["角色版本", "系列封面", "场景记忆"],
  };

  if (!apiAvailable) {
    const project = normalizeProject({ id: `local-project-${projects.length + 1}`, status: "active", ...body, character_ids: [activeCharacterId] });
    projects = [...projects, project];
    activeProjectId = project.id;
    renderProjectsPanel();
    apiStatus.textContent = `${project.name} 已创建`;
    return;
  }

  try {
    const response = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const project = normalizeProject(payload.project);
    projects = [...projects, project];
    activeProjectId = project.id;
    renderProjectsPanel();
    apiStatus.textContent = `${project.name} 已创建`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function bindActiveCharacterToProject() {
  const project = projects.find((item) => item.id === activeProjectId);
  if (!project) return;
  const characterIds = [...new Set([...(project.character_ids || []), activeCharacterId])];

  if (!apiAvailable) {
    project.character_ids = characterIds;
    project.counts.characters = characterIds.length;
    renderProjectsPanel();
    apiStatus.textContent = `${characterName.textContent} 已加入项目`;
    return;
  }

  try {
    const response = await fetch(`/api/projects/${project.id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ character_ids: characterIds }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    projects = projects.map((item) => (item.id === project.id ? normalizeProject(payload.project) : item));
    renderProjectsPanel();
    apiStatus.textContent = `${characterName.textContent} 已加入项目`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function updateProjectReview(reviewAction) {
  const project = projects.find((item) => item.id === activeProjectId);
  if (!project) return;

  if (!apiAvailable) {
    const updatedProject = normalizeProject(applyLocalProjectReview(project, reviewAction));
    projects = projects.map((item) => (item.id === project.id ? updatedProject : item));
    renderProjectsPanel();
    apiStatus.textContent = projectReviewActionLabel(reviewAction);
    return;
  }

  try {
    const response = await fetch(`/api/projects/${project.id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_action: reviewAction }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    projects = projects.map((item) => (item.id === project.id ? normalizeProject(payload.project) : item));
    renderProjectsPanel();
    apiStatus.textContent = projectReviewActionLabel(reviewAction);
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function refreshCharactersFromApi() {
  if (!apiAvailable) return;
  const response = await fetch("/api/characters");
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `API ${response.status}`);
  }
  characters = (payload.characters || []).map(normalizeCharacter);
  renderCharacterList();
  setCharacter(activeCharacterId);
}

async function trainProductionIdentity() {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能训练生产身份包";
    return;
  }
  apiStatus.textContent = "正在训练生产身份包...";
  try {
    const response = await fetch("/api/identity-training/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ character_id: "all" }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    await refreshCharactersFromApi();
    await showSystemReadiness();
    apiStatus.textContent = `生产身份包已训练：${Number(payload.training?.trained || 0)}/${Number(payload.training?.total || 0)} 角色`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

let loraTrainArmed = false;
let loraTrainArmTimer = null;

async function trainCharacterLora() {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能训练角色 LoRA";
    return;
  }
  const character = characters.find((item) => item.id === activeCharacterId);
  const name = character?.name || activeCharacterId;
  // Paid action: window.confirm() does not work in the native WKWebView shell
  // (no JS confirm-panel delegate), so guard with a two-click confirm instead.
  if (!loraTrainArmed) {
    loraTrainArmed = true;
    apiStatus.textContent = `再点一次「训练角色 LoRA」确认：将用 ${name} 的参考脸调用 fal 付费训练（约几分钟，消耗你的 fal 额度）`;
    clearTimeout(loraTrainArmTimer);
    loraTrainArmTimer = setTimeout(() => {
      loraTrainArmed = false;
    }, 8000);
    return;
  }
  loraTrainArmed = false;
  clearTimeout(loraTrainArmTimer);
  apiStatus.textContent = `正在为 ${name} 训练角色 LoRA，预计几分钟，请保持应用打开...`;
  try {
    const response = await fetch("/api/identity-training/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ character_id: activeCharacterId, train_lora: true }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    await refreshCharactersFromApi();
    await showSystemReadiness();
    const trained = payload.jobs?.find((job) => job.lora_trained);
    apiStatus.textContent = trained
      ? `${name} 的角色 LoRA 已训练完成（触发词 ${trained.fal_lora?.trigger_word || ""}），新生成将自动锁脸`
      : `${name} 训练已提交`;
  } catch (error) {
    apiStatus.textContent = `角色 LoRA 训练失败：${error.message}`;
  }
}

async function initializeDeployment() {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能初始化部署";
    return;
  }
  apiStatus.textContent = "正在初始化部署存储与权限...";
  try {
    const response = await fetch("/api/deployment/initialize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_id: "persona-studio-local-prod" }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    await showSystemReadiness();
    apiStatus.textContent = payload.ready ? "部署、共享存储、RBAC 和审计日志已就绪" : "部署初始化完成，仍需复核";
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

function releaseTargetProject() {
  return projects.find((item) => item.id === activeProjectId)
    || projects.find((item) => item.user_segment === "商业用户")
    || projects[0];
}

async function buildReleasePackage() {
  const project = releaseTargetProject();
  if (!project) {
    apiStatus.textContent = "暂无项目可构建发布包";
    return;
  }
  if (!apiAvailable) {
    const release = {
      id: `local-release-${Date.now()}`,
      status: "ready",
      label: "本地预览发布包",
      built_at: new Date().toISOString(),
      artifact_path: "local-preview",
      checklist: [],
    };
    projects = projects.map((item) => (
      item.id === project.id
        ? normalizeProject({ ...item, status: "approved", release_package: release })
        : item
    ));
    activeProjectId = project.id;
    renderProjectsPanel();
    apiStatus.textContent = `${project.name} 发布包已构建（本地预览）`;
    return;
  }
  apiStatus.textContent = `正在构建发布包：${project.name}`;
  try {
    const response = await fetch(`/api/projects/${project.id}/release`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ auto_train_identity: true, ensure_deployment: true }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const normalizedProject = normalizeProject(payload.project);
    projects = projects.map((item) => (item.id === normalizedProject.id ? normalizedProject : item));
    if (!projects.some((item) => item.id === normalizedProject.id)) {
      projects = [...projects, normalizedProject];
    }
    activeProjectId = normalizedProject.id;
    await refreshCharactersFromApi();
    if (workspaceTitle.textContent === "系统状态") {
      await showSystemReadiness();
    } else {
      renderProjectsPanel();
    }
    apiStatus.textContent = `${normalizedProject.name} ${projectReleaseLabel(normalizedProject)} · ${compactPath(payload.release_package?.artifact_path || "")}`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

async function exportIpPackage() {
  const project = projects.find((item) => item.id === activeProjectId);
  if (!project) return;

  try {
    let payloadProject = project;
    if (apiAvailable) {
      const response = await fetch(`/api/projects/${project.id}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || `API ${response.status}`);
      }
      payloadProject = payload.project;
    }
    const ipPackage = payloadProject.ip_package || {
      project_id: project.id,
      name: project.name,
      user_segment: project.user_segment,
      deliverables: project.deliverables,
      character_ids: project.character_ids,
    };
    downloadJson(ipPackage, `${project.id}-ip-package.json`);
    const normalizedProject = normalizeProject({ ...payloadProject, ip_package: ipPackage });
    projects = projects.map((item) => (item.id === project.id ? normalizedProject : item));
    if (workspaceTitle.textContent === "项目") {
      renderProjectsPanel();
    }
    const assetCounts = projectAssetCounts(normalizedProject);
    apiStatus.textContent = `IP 包已导出：${project.name} · ${assetCounts.characters} 角色 · ${assetCounts.generated_images} 图`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

function renderWorksPanel() {
  const failedCount = generationJobs.filter((job) => job.status === "failed").length;
  const runningCount = generationJobs.filter((job) => job.status === "running").length;
  const completedCount = generationJobs.filter((job) => job.status === "completed").length;
  const jobSummary = generationJobs.length
    ? `${generationJobs.length} 个任务 · ${completedCount} 完成 · ${failedCount} 失败`
    : "查看生成请求、失败原因和重试入口";
  workspaceModePanel.innerHTML = `
    <div class="quick-card-grid">
      <button class="quick-card" type="button" data-workspace-action="all">
        <strong>全部作品</strong>
        <span>显示所有生成记录</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="favorites">
        <strong>收藏作品</strong>
        <span>只看已收藏图片</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="jobs">
        <strong>生成任务</strong>
        <span>${runningCount ? `${runningCount} 个进行中` : jobSummary}</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="asset-library">
        <strong>资产库</strong>
        <span>搜索角色、生成图、参考图、记忆、项目和任务</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="system-readiness">
        <strong>系统状态</strong>
        <span>查看本地完成度、模块闭环和外部依赖</span>
      </button>
      <button class="quick-card" type="button" data-workspace-action="export">
        <strong>导出项目</strong>
        <span>下载角色、LoRA 与生成记录</span>
      </button>
    </div>
  `;
}

async function showSystemReadiness() {
  showWorkspaceSurface("系统状态");
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>系统状态</strong>
        <span>正在读取本地 Character OS 完成度</span>
      </div>
    </div>
  `;

  if (!apiAvailable) {
    workspaceModePanel.innerHTML = `<div class="empty-state">需要后端连接才能计算系统状态</div>`;
    apiStatus.textContent = "后端未连接";
    return;
  }

  try {
    const response = await fetch("/api/system/readiness");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    systemReadiness = payload;
    renderSystemReadinessPanel(payload);
    apiStatus.textContent = `系统状态：本地完成度 ${Number(payload.completion_percent || 0)}%`;
  } catch (error) {
    workspaceModePanel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    apiStatus.textContent = error.message;
  }
}

function renderSystemReadinessPanel(readiness) {
  const totals = readiness?.totals || {};
  const modules = Array.isArray(readiness?.modules) ? readiness.modules : [];
  const dependencies = Array.isArray(readiness?.external_dependencies) ? readiness.external_dependencies : [];
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>Character OS 本地状态</strong>
        <span>${escapeHtml(readiness?.summary || "本地状态已生成")}</span>
      </div>
      <div class="project-review-actions">
        <button class="secondary-button" type="button" data-workspace-action="train-production-identity">训练身份包</button>
        <button class="secondary-button" type="button" data-workspace-action="train-character-lora">训练角色 LoRA（锁脸）</button>
        <button class="secondary-button" type="button" data-workspace-action="initialize-deployment">初始化部署</button>
        <button class="secondary-button" type="button" data-workspace-action="build-release-package">构建发布包</button>
        <button class="secondary-button" type="button" data-workspace-action="system-readiness">刷新</button>
      </div>
    </div>
    <div class="readiness-summary is-${escapeAttribute(readiness?.status || "needs_review")}">
      <strong>${Number(readiness?.completion_percent || 0)}%</strong>
      <span>${escapeHtml(readinessStatusLabel(readiness?.status))}</span>
      <span>${Number(totals.characters || 0)} 角色 · ${Number(totals.generations || 0)} 图 · ${Number(totals.asset_total || 0)} 资产 · ${Number(totals.credits_remaining || 0)} 点</span>
    </div>
    <div class="readiness-grid">
      ${modules.map(readinessModuleCard).join("")}
    </div>
    <div class="readiness-dependency-list">
      <div class="workspace-panel-head compact">
        <strong>外部依赖</strong>
        <span>不影响本地闭环，但影响生产上线</span>
      </div>
      ${dependencies.map(readinessDependencyRow).join("")}
    </div>
    ${providerHealthSection(readiness?.provider_health)}
  `;
}

function readinessModuleCard(module) {
  const evidence = (module.evidence || []).slice(0, 3).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  const nextStep = module.next_step ? `<small>${escapeHtml(module.next_step)}</small>` : "";
  return `
    <article class="readiness-card is-${escapeAttribute(module.status || "review")}">
      <div>
        <strong>${escapeHtml(module.label || module.id || "模块")}</strong>
        <span>${escapeHtml(readinessStatusLabel(module.status))} · ${Number(module.score || 0)}%</span>
      </div>
      <div class="readiness-evidence">${evidence}</div>
      ${nextStep}
    </article>
  `;
}

function readinessDependencyRow(dependency) {
  return `
    <article class="readiness-dependency is-${escapeAttribute(dependency.status || "optional")}">
      <div>
        <strong>${escapeHtml(dependency.label || dependency.id || "依赖")}</strong>
        <span>${escapeHtml(readinessStatusLabel(dependency.status))} · ${escapeHtml(dependency.provider || "未配置")}${dependency.model ? ` · ${escapeHtml(dependency.model)}` : ""}</span>
      </div>
      <span>${escapeHtml(dependency.note || "")}</span>
    </article>
  `;
}

function providerHealthSection(health) {
  const summary = health?.summary || {};
  const total = Number(summary.total || 0);
  if (!total) return "";
  return `
    <div class="provider-health-section">
      <div class="workspace-panel-head compact">
        <strong>Provider 健康</strong>
        <span>${Number(summary.passed || 0)} 通过 · ${Number(summary.failed || 0)} 失败 · ${Number(summary.untested || 0)} 未实测</span>
      </div>
      ${providerHealthRowsMarkup(health)}
    </div>
  `;
}

function readinessStatusLabel(status) {
  return {
    local_complete: "本地完成",
    local_ready: "本地可交付",
    needs_review: "需要复核",
    ready: "已闭环",
    production_local_ready: "本地生产就绪",
    not_configured: "未配置",
    not_started: "未开始",
    partial: "部分完成",
    review: "需复核",
    incomplete: "未完成",
    configured: "已配置",
    passed: "通过",
    missing: "缺失",
    pending: "待处理",
    optional: "可选",
    external_required: "需外部生产接入",
    local_persistent: "本地持久化",
    memory_only: "内存态",
  }[status] || localizeLabel(status || "未标注");
}

async function showAssetLibrary() {
  showWorkspaceSurface("资产库");
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>资产库</strong>
        <span>正在索引角色、生成图、参考图、记忆、项目和任务</span>
      </div>
    </div>
  `;

  if (!apiAvailable) {
    workspaceModePanel.innerHTML = `<div class="empty-state">需要后端连接才能打开统一资产库</div>`;
    apiStatus.textContent = "后端未连接";
    return;
  }

  try {
    const response = await fetch("/api/assets/library");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    assetLibrary = {
      summary: payload.summary || {},
      filters: payload.filters || { types: [] },
      items: Array.isArray(payload.items) ? payload.items : [],
    };
    renderAssetLibraryPanel();
    apiStatus.textContent = `资产库已打开 · ${assetLibrary.summary.total || assetLibrary.items.length} 个资产`;
  } catch (error) {
    workspaceModePanel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    apiStatus.textContent = error.message;
  }
}

function renderAssetLibraryPanel() {
  const summary = assetLibrary.summary || {};
  const typeOptions = assetLibraryTypeOptions();
  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <div>
        <strong>统一资产库</strong>
        <span>${Number(summary.total || assetLibrary.items.length)} 总数 · ${Number(summary.generation || 0)} 图 · ${Number(summary.reference || 0)} 参考 · ${Number(summary.memory || 0)} 记忆</span>
      </div>
      <button class="secondary-button" type="button" data-workspace-action="asset-library">刷新</button>
    </div>
    <div class="asset-library-toolbar">
      <label class="control-field">
        <span>搜索</span>
        <input id="assetLibrarySearch" type="search" value="${escapeAttribute(assetLibraryQuery)}" placeholder="角色、提示词、状态、标签" />
      </label>
      <label class="control-field">
        <span>类型</span>
        <select id="assetLibraryType">
          ${typeOptions.map((option) => `
            <option value="${escapeAttribute(option.id)}" ${option.id === assetLibraryType ? "selected" : ""}>${escapeHtml(option.label)} · ${Number(option.count || 0)}</option>
          `).join("")}
        </select>
      </label>
    </div>
    <div class="asset-library-stats" id="assetLibraryStats"></div>
    <div class="asset-library-list" id="assetLibraryRows"></div>
  `;
  renderAssetLibraryRows();
}

function assetLibraryTypeOptions() {
  const options = assetLibrary.filters?.types || [];
  if (options.length) return options;
  return [
    { id: "all", label: "全部", count: assetLibrary.items.length },
    { id: "character", label: "角色", count: 0 },
    { id: "generation", label: "生成图", count: 0 },
    { id: "reference", label: "参考图", count: 0 },
    { id: "memory", label: "记忆", count: 0 },
    { id: "project", label: "项目", count: 0 },
    { id: "job", label: "任务", count: 0 },
  ];
}

function renderAssetLibraryRows() {
  const rows = document.querySelector("#assetLibraryRows");
  const stats = document.querySelector("#assetLibraryStats");
  if (!rows || !stats) return;

  const visible = filteredAssetLibraryItems();
  stats.textContent = `${visible.length} 个匹配 · ${assetLibraryTypeLabel(assetLibraryType)} · ${assetLibraryQuery.trim() || "无关键词"}`;
  rows.innerHTML = visible.length
    ? visible.slice(0, 80).map(assetLibraryRowMarkup).join("")
    : `<div class="job-empty-state"><strong>没有匹配资产</strong><span>换一个关键词或类型筛选。</span></div>`;
}

function filteredAssetLibraryItems() {
  const query = assetLibraryQuery.trim().toLowerCase();
  return (assetLibrary.items || []).filter((item) => {
    const typeMatch = assetLibraryType === "all" || item.type === assetLibraryType;
    const queryMatch = !query || String(item.search_text || `${item.title} ${item.subtitle} ${(item.tags || []).join(" ")}`).toLowerCase().includes(query);
    return typeMatch && queryMatch;
  });
}

function assetLibraryRowMarkup(item) {
  const image = item.image ? `<img src="${escapeAttribute(normalizeAssetPath(item.image))}" alt="${escapeAttribute(item.title || "资产")}" />` : `<span class="asset-library-icon">${escapeHtml(assetLibraryTypeLabel(item.type).slice(0, 2))}</span>`;
  const tags = (item.tags || []).slice(0, 4).map((tag) => `<span>${escapeHtml(localizeLabel(tag))}</span>`).join("");
  const primary = assetLibraryPrimaryAction(item);
  return `
    <article class="asset-library-row is-${escapeAttribute(item.type || "asset")}">
      <div class="asset-library-thumb">${image}</div>
      <div class="asset-library-main">
        <strong>${escapeHtml(item.title || item.id || "资产")}</strong>
        <span>${escapeHtml(item.subtitle || item.character_name || item.id || "")}</span>
        <div class="asset-library-tags">
          <span>${escapeHtml(assetLibraryTypeLabel(item.type))}</span>
          <span>${escapeHtml(assetLibraryStatusLabel(item.status))}</span>
          ${tags}
        </div>
      </div>
      <button class="secondary-button" type="button" data-asset-open="${escapeAttribute(primary.type)}" data-asset-id="${escapeAttribute(primary.id)}">${escapeHtml(primary.label)}</button>
    </article>
  `;
}

function assetLibraryPrimaryAction(item) {
  if (item.type === "generation") return { type: "generation", id: item.id, label: "打开图" };
  if (item.type === "character") return { type: "character", id: item.id, label: "打开角色" };
  if (item.type === "project") return { type: "project", id: item.id, label: "打开项目" };
  if (item.type === "job") return { type: "job", id: item.id, label: "打开任务" };
  if (item.type === "memory") return { type: "memory", id: item.character_id, label: "管理记忆" };
  return { type: "character", id: item.character_id || activeCharacterId, label: "查看角色" };
}

async function openAssetLibraryItem(type, id) {
  if (type === "generation") {
    openGenerationFromJob(id);
    return;
  }
  if (type === "character") {
    const character = characters.find((item) => item.id === id);
    if (!character) {
      apiStatus.textContent = `未找到角色：${id}`;
      return;
    }
    activeCharacterId = id;
    setCharacter(id);
    renderCharacterList();
    showGenerationResultsPanel();
    renderGenerationGrid();
    apiStatus.textContent = `已打开角色：${character.name}`;
    return;
  }
  if (type === "project") {
    await selectProject(id);
    return;
  }
  if (type === "job") {
    await showGenerationJobs();
    apiStatus.textContent = `已打开任务列表：${id}`;
    return;
  }
  if (type === "memory") {
    await showMemoryStorePanel(id || activeCharacterId);
  }
}

function assetLibraryTypeLabel(type) {
  return {
    all: "全部",
    character: "角色",
    generation: "生成图",
    reference: "参考图",
    memory: "记忆",
    project: "项目",
    job: "任务",
  }[type] || "资产";
}

function assetLibraryStatusLabel(status) {
  const labels = {
    pass: "通过",
    review: "复核",
    fail: "失败",
    ready: "就绪",
    active: "启用",
    stored: "已存",
    completed: "已完成",
    failed: "失败",
    running: "进行中",
    approved: "已批准",
    draft: "草稿",
    in_review: "审阅中",
  };
  return labels[status] || localizeLabel(status || "未标注");
}

async function showGenerationJobs() {
  if (apiAvailable) {
    try {
      await loadGenerationJobs();
    } catch (error) {
      apiStatus.textContent = error.message;
    }
  }
  showWorkspaceSurface("生成任务");
  renderGenerationJobsPanel();
  apiStatus.textContent = generationJobs.length ? `已打开 ${generationJobs.length} 个生成任务` : "暂无生成任务";
}

function renderGenerationJobsPanel() {
  const jobs = generationJobs.slice(0, 12);
  const failedCount = generationJobs.filter((job) => job.status === "failed").length;
  const completedCount = generationJobs.filter((job) => job.status === "completed").length;
  const runningCount = generationJobs.filter((job) => job.status === "running").length;
  const body = jobs.length
    ? jobs.map((job) => generationJobCard(job)).join("")
    : `
      <div class="job-empty-state">
        <strong>暂无生成任务</strong>
        <span>从现在开始的新生成会记录任务状态、耗时、模型路由和失败原因。</span>
      </div>
    `;

  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <strong>生成任务</strong>
      <span>${generationJobs.length} 总数 · ${completedCount} 完成 · ${failedCount} 失败 · ${runningCount} 进行中</span>
    </div>
    <div class="job-card-list">
      ${body}
    </div>
  `;
}

function generationJobCard(job) {
  const status = job.status || "unknown";
  const prompt = job.prompt || job.request?.prompt || "未记录提示词";
  const route = job.model_route ? shortModelRouteLabel(job.model_route) : job.image_model_label || "等待模型路由";
  const quality = job.quality_summary || {};
  const billing = job.billing || {};
  const resultCount = Number(job.result_count ?? (job.generation_ids || []).length ?? 0);
  const generationButtons = (job.generation_ids || []).slice(0, 4).map((id) => `
    <button class="job-generation-link" type="button" data-open-generation-id="${escapeAttribute(id)}">${escapeHtml(id)}</button>
  `).join("");
  const retryButton = status === "failed"
    ? `<button class="secondary-button" type="button" data-retry-job-id="${escapeAttribute(job.id)}">重试</button>`
    : "";
  const errorMarkup = job.error ? `<span class="job-error">${escapeHtml(job.error)}</span>` : "";
  const qualityMarkup = quality.total
    ? `<span>质检 ${quality.passed}/${quality.total} · 最低 ${Math.round(Number(quality.lowest_score || 0) * 100)}%</span>`
    : `<span>质检未生成</span>`;
  const billingMarkup = billing.status === "charged" && Number(billing.cost || 0) > 0
    ? `<span>扣费：${Number(billing.cost)} 点 · ${Number(billing.credits_before || 0)} → ${Number(billing.credits_after || 0)}</span>`
    : Number(billing.cost || 0) > 0
      ? `<span>扣费：未扣费 · 预估 ${Number(billing.cost)} 点</span>`
      : `<span>扣费：未生成</span>`;

  return `
    <article class="job-card is-${escapeAttribute(status)}">
      <div class="job-card-head">
        <div>
          <strong>${escapeHtml(job.id || "job")}</strong>
          <span>${jobStatusLabel(status)} · ${compactDateTime(job.requested_at)} · ${Number(job.duration_ms || 0)}ms</span>
        </div>
        <span class="job-status-pill">${jobStatusLabel(status)}</span>
      </div>
      <div class="job-meta-grid">
        <span>角色：${escapeHtml(characterLabel(job.character_id))}</span>
        <span>模式：${escapeHtml(localizeLabel(job.mode || "文生图"))}</span>
        <span>数量：${Number(job.count || resultCount || 0)}</span>
        <span>尺寸：${escapeHtml(job.size || "未记录")}</span>
        <span>模型：${escapeHtml(route)}</span>
        ${qualityMarkup}
        ${billingMarkup}
      </div>
      <p>${escapeHtml(prompt)}</p>
      ${errorMarkup}
      <div class="job-action-row">
        ${generationButtons || `<span>暂无生成图</span>`}
        ${retryButton}
      </div>
    </article>
  `;
}

async function retryGenerationJob(jobId) {
  if (!apiAvailable) {
    apiStatus.textContent = "需要后端连接才能重试任务";
    return;
  }
  try {
    const response = await fetch(`/api/generation-jobs/${jobId}/retry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const created = payload.generations || [];
    if (payload.account) {
      setAccountState(payload.account);
    }
    generations = [...created, ...generations];
    latestGenerationIds = new Set(created.map((generation) => generation.id).filter(Boolean));
    await loadGenerationJobs();
    renderGenerationJobsPanel();
    renderGenerationGrid();
    apiStatus.textContent = `任务 ${jobId} 已重试为 ${payload.job?.id || "新任务"}`;
  } catch (error) {
    apiStatus.textContent = error.message;
    await loadGenerationJobs().catch(() => {});
    renderGenerationJobsPanel();
  }
}

function openGenerationFromJob(generationId) {
  const generation = generations.find((item) => item.id === generationId);
  if (!generation) {
    apiStatus.textContent = `未找到生成图：${generationId}`;
    return;
  }
  openGenerationDetail(generation);
}

function jobStatusLabel(status) {
  if (status === "completed") return "已完成";
  if (status === "failed") return "失败";
  if (status === "running") return "进行中";
  return "未知";
}

function characterLabel(characterId) {
  return characters.find((character) => character.id === characterId)?.name || characterId || "未记录";
}

function renderVersionHistoryPanel(versions) {
  versionSnapshots = versions.slice().sort((left, right) => Number(left.version || 0) - Number(right.version || 0));
  showWorkspaceSurface("版本历史");
  const currentVersion = Math.max(...versionSnapshots.map((version) => Number(version.version || 0)), 0);
  const selectedVersion = versionSnapshots.find((version) => Number(version.version) === currentVersion) || versionSnapshots.at(-1);
  const cards = versionSnapshots.length
    ? versionSnapshots.slice().reverse().map((version) => `
      <div class="quick-card version-card${Number(version.version) === Number(selectedVersion?.version) ? " active" : ""}">
        <button class="version-select" type="button" data-version-number="${version.version}">
          <strong>v${version.version}</strong>
          <small>${versionStatusText(version, currentVersion)}</small>
        </button>
        <button
          class="version-restore"
          type="button"
          data-version-restore="${version.version}"
          ${version.can_restore && Number(version.version) !== Number(currentVersion) ? "" : "disabled"}
          aria-label="恢复到 v${version.version}"
        >恢复</button>
      </div>
    `).join("")
    : `
      <button class="quick-card active" type="button" data-version-number="0">
        <strong>暂无历史</strong>
        <span>点击继续训练会生成新的角色版本</span>
      </button>
    `;

  workspaceModePanel.innerHTML = `
    <div class="workspace-panel-head">
      <strong>${characterName.textContent} 版本历史</strong>
      <span>版本快照来自本地角色资产</span>
    </div>
    <div class="quick-card-grid">
      ${cards}
    </div>
    <div class="version-compare-band" id="versionCompareBand">
      ${selectedVersion ? versionCompareMarkup(selectedVersion, currentVersion) : "暂无可比较版本"}
    </div>
  `;
}

function selectVersionSnapshot(versionNumber) {
  const selected = versionSnapshots.find((version) => Number(version.version) === Number(versionNumber));
  if (!selected) return;
  workspaceModePanel.querySelectorAll(".version-card").forEach((card) => {
    const button = card.querySelector("[data-version-number]");
    card.classList.toggle("active", Number(button?.dataset.versionNumber) === Number(versionNumber));
  });
  const currentVersion = Math.max(...versionSnapshots.map((version) => Number(version.version || 0)), 0);
  const compareBand = document.querySelector("#versionCompareBand");
  if (compareBand) {
    compareBand.innerHTML = versionCompareMarkup(selected, currentVersion);
  }
  apiStatus.textContent = `已选中 v${selected.version} · ${selected.note || "版本快照"}`;
}

async function restoreVersion(versionNumber) {
  const snapshot = versionSnapshots.find((version) => Number(version.version) === Number(versionNumber));
  if (!snapshot?.can_restore) {
    apiStatus.textContent = `v${versionNumber} 缺少完整快照，不能恢复`;
    return;
  }
  try {
    const response = await fetch(`/api/characters/${activeCharacterId}/versions/${versionNumber}/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: `从 v${versionNumber} 恢复` }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `API ${response.status}`);
    }
    const updated = normalizeCharacter(payload.character);
    characters = characters.map((item) => (item.id === updated.id ? updated : item));
    setCharacter(updated.id);
    renderCharacterList();
    renderGenerationGrid();
    renderVersionHistoryPanel(payload.versions || updated.versions || []);
    apiStatus.textContent = `${updated.name} 已从 v${versionNumber} 恢复为 v${updated.version}`;
  } catch (error) {
    apiStatus.textContent = error.message;
  }
}

function versionStatusText(version, currentVersion) {
  if (Number(version.version) === Number(currentVersion)) return "当前版本";
  return version.can_restore ? "可恢复" : "只读快照";
}

function versionCompareMarkup(version, currentVersion) {
  const summary = version.summary || {};
  return `
    <div>
      <strong>v${version.version} ${Number(version.version) === Number(currentVersion) ? "当前" : version.can_restore ? "可恢复" : "只读"}</strong>
      <span>${version.note || "版本快照"}</span>
    </div>
    <div class="project-meta-grid">
      <span>参考图：${summary.identity_reference_count ?? version.identity_reference_count ?? 0}</span>
      <span>风格：${localizeLabel(summary.style_preset || version.style_preset || "未记录")}</span>
      <span>LoRA：${labelForLora(summary.lora_id || version.lora_id) || summary.lora_id || version.lora_id || "未启用"}</span>
      <span>一致性：${Math.round(Number(summary.consistency_score ?? version.consistency_score ?? 0) * 100)}%</span>
    </div>
  `;
}

function renderModelPlazaPanel(options = {}) {
  const creatorPlan = accountPlans.find((plan) => plan.id === "upgrade-creator") || demoPlans["upgrade-creator"];
  const businessPlan = accountPlans.find((plan) => plan.id === "upgrade-business") || demoPlans["upgrade-business"];
  const planMarkup = options.showPlans ? `
    <div class="workspace-panel-head plan-head">
      <strong>升级方案</strong>
      <span>${apiAvailable ? "账户额度由后端持久化，生成会扣减余额" : "本地演示立即生效，额度会保存在浏览器"}</span>
    </div>
    <div class="quick-card-grid plan-grid">
      <button class="quick-card plan-card${accountState.plan_id === "upgrade-creator" ? " active" : ""}" type="button" data-workspace-action="upgrade-creator">
        <strong>${escapeHtml(creatorPlan.label || "创作者 Pro")}</strong>
        <span>${Number(creatorPlan.monthly_credits || creatorPlan.credits || 2000)} 点/月 · ${(creatorPlan.features || []).slice(0, 2).join(" · ")}</span>
      </button>
      <button class="quick-card plan-card${accountState.plan_id === "upgrade-business" ? " active" : ""}" type="button" data-workspace-action="upgrade-business">
        <strong>${escapeHtml(businessPlan.label || "商业团队")}</strong>
        <span>${Number(businessPlan.monthly_credits || businessPlan.credits || 8000)} 点/月 · ${(businessPlan.features || []).slice(0, 2).join(" · ")}</span>
      </button>
    </div>
  ` : "";
  workspaceModePanel.innerHTML = `
    <div class="model-plaza-panel">
      <div class="workspace-panel-head">
        <strong>模型与 LoRA</strong>
        <span>选择后会同步到左侧风格控制，不触发真实生成</span>
      </div>
      <div class="quick-card-grid model-lora-grid">
        ${loras.map((lora) => `
          <button class="quick-card" type="button" data-use-lora="${lora.id}">
            <strong>${lora.label || lora.name}</strong>
            <span>默认权重 ${Number(lora.default_weight || lora.weight || 0).toFixed(2)}</span>
          </button>
        `).join("")}
      </div>
    </div>
    ${planMarkup}
  `;
}

function setActiveNavByName(name) {
  const target = [...navItems].find((button) => button.dataset.nav === name);
  if (target) {
    setActiveButton(navItems, target);
  }
}

function setReferenceKind(kind) {
  if (!referenceCategories[kind]) return;
  activeReferenceKind = kind;
  referenceKindTabs.querySelectorAll("[data-reference-kind]").forEach((button) => {
    button.classList.toggle("active", button.dataset.referenceKind === kind);
  });
  renderReferenceRail();
  apiStatus.textContent = `参考类型：${referenceCategories[kind].label}`;
}

function renderReferenceRail() {
  const category = referenceCategories[activeReferenceKind] || referenceCategories.face;
  if (referenceRailHint) {
    referenceRailHint.textContent = category.hint;
  }
  referenceList.replaceChildren(
    ...category.items.map((item) => referenceCardForItem(activeReferenceKind, item)),
    addReferenceButton(category),
  );
  updateReferenceDraggables();
}

function applyCharacterReferenceAssets(character) {
  referenceCategories.face.items = normalizeReferenceAssets(character.reference_assets, character.id);
  renderIdentityStripFromReferences();
  if (activeReferenceKind === "face") {
    renderReferenceRail();
  }
}

function applyCharacterReferenceCollections(character) {
  const collections = normalizeReferenceCollections(character.reference_collections);
  referenceCollectionKinds.forEach((kind) => {
    if (referenceCategories[kind]) {
      referenceCategories[kind].items = collections[kind];
    }
  });
  if (referenceCollectionKinds.includes(activeReferenceKind)) {
    renderReferenceRail();
  }
}

function renderIdentityStripFromReferences() {
  const faceItems = referenceCategories.face.items;
  identityStrip.replaceChildren(
    ...faceItems.map((item, index) => identityReferenceButton(item, index)),
    identityAddButton(),
  );
}

function renderIdentityReadiness(readiness) {
  if (!identityReadiness) return;
  const status = readiness?.status || "incomplete";
  const checks = readiness?.checks || [];
  const failedCheck = checks.find((check) => check.status === "failed" || check.status === "review");
  identityReadiness.className = `identity-readiness is-${status}`;
  identityReadiness.innerHTML = `
    <strong>${escapeHtml(readiness?.label || "参考脸不足")}</strong>
    <span>${Number(readiness?.reference_count || 0)} 张 · 分数 ${Math.round(Number(readiness?.score || 0) * 100)}%${failedCheck ? ` · ${escapeHtml(failedCheck.label)}` : ""}</span>
  `;
}

function identityReferenceButton(item, index) {
  const button = document.createElement("button");
  button.className = `face-reference ${item.active ? "active" : ""}`.trim();
  button.type = "button";
  button.dataset.ref = item.label || `参考 ${index + 1}`;
  button.dataset.referenceKind = "face";
  button.dataset.referenceId = item.id;
  button.dataset.referenceLabel = item.label || `参考 ${index + 1}`;
  button.dataset.referencePrompt = item.prompt || "";

  const image = document.createElement("img");
  image.src = displayAssetPath(item.image);
  image.alt = `${item.label || "身份参考脸"} ${index + 1}`;
  const label = document.createElement("span");
  label.textContent = item.label || `参考 ${index + 1}`;
  const replaceAction = document.createElement("span");
  replaceAction.className = "replace-reference";
  replaceAction.dataset.action = "replace-reference";
  replaceAction.textContent = "替换";
  const removeAction = document.createElement("span");
  removeAction.className = "remove-reference";
  removeAction.dataset.action = "remove-reference";
  removeAction.textContent = "移除";
  button.append(image, label, replaceAction, removeAction);
  return button;
}

function identityAddButton() {
  const button = document.createElement("button");
  button.className = "face-reference add-face";
  button.type = "button";
  button.textContent = "+";
  return button;
}

function displayAssetPath(path) {
  if (!path) return "./assets/persona-ref-1.png";
  if (path.startsWith("data:image/") || path.startsWith("http")) return path;
  return path.startsWith("./") ? path : `./${path}`;
}

function referenceCardForItem(kind, item) {
  const button = document.createElement("button");
  button.className = `reference-card ${item.active ? "active" : ""}`.trim();
  button.type = "button";
  button.draggable = true;
  button.dataset.referenceKind = kind;
  button.dataset.referenceId = item.id;
  button.dataset.referencePrompt = item.prompt || "";
  button.dataset.referenceLabel = item.label || referenceCategories[kind]?.label || "参考图";
  if (item.image) {
    const image = document.createElement("img");
    image.src = displayAssetPath(item.image);
    image.alt = item.alt || item.label || "参考图";
    button.append(image);
  } else {
    const visual = document.createElement("i");
    visual.className = `reference-visual ${item.visual || ""}`.trim();
    visual.setAttribute("aria-hidden", "true");
    button.append(visual);
  }
  const label = document.createElement("span");
  label.textContent = item.label || referenceCategories[kind]?.label || "参考";
  const replaceAction = document.createElement("span");
  replaceAction.className = "replace-reference";
  replaceAction.dataset.action = "replace-reference";
  replaceAction.textContent = "替换";
  const removeAction = document.createElement("span");
  removeAction.className = "remove-reference";
  removeAction.dataset.action = "remove-reference";
  removeAction.textContent = "移除";
  button.append(label, replaceAction, removeAction);
  return button;
}

function addReferenceButton(category) {
  const button = document.createElement("button");
  button.className = "reference-card add-reference";
  button.type = "button";
  button.textContent = "+";
  button.setAttribute("aria-label", category.uploadLabel || "上传参考图");
  return button;
}

function activeReferenceCards() {
  return [...referenceList.querySelectorAll(".reference-card:not(.add-reference)")];
}

function selectedReferenceGuidance() {
  syncActiveReferenceSelectionFromDom();
  const promptSubject = promptSubjectHint(promptInput.value);
  const allowFaceReferences = referenceToggle.getAttribute("aria-pressed") === "true" && isCharacterPromptSubject(promptSubject);
  return Object.entries(referenceCategories).map(([kind, category]) => ({
    kind,
    label: category.label,
    items: category.items
      .filter((item) => item.active)
      .filter(() => kind !== "face" || allowFaceReferences)
      .map((item) => ({
        id: item.id,
        label: item.label,
        prompt: item.prompt || "",
        ...(item.image ? { image: item.image.replace(/^\.\//, "") } : {}),
      })),
  })).filter((group) => group.items.length);
}

function promptSubjectHint(prompt) {
  const text = String(prompt || "").toLowerCase();
  if (["男人", "男性", "男孩", "男士", "父亲", "man", "male", "boy", "gentleman"].some((token) => text.includes(token))) return "male";
  if (["儿童", "小孩", "孩子", "child", "kid"].some((token) => text.includes(token))) return "child";
  if (["汽车", "跑车", "轿车", "车辆", "车 ", "car", "vehicle", "sports car"].some((token) => text.includes(token))) return "car";
  if ([
    "产品",
    "商品",
    "包装",
    "香水",
    "瓶子",
    "单页",
    "落地页",
    "详情页",
    "广告页",
    "保健品",
    "海参",
    "电商",
    "product",
    "bottle",
    "package",
    "landing page",
    "single page",
    "advertorial",
  ].some((token) => text.includes(token))) return "product";
  if (["风景", "山", "大海", "海边", "海岸", "海面", "森林", "城市", "建筑", "landscape", "mountain", "city", "building"].some((token) => text.includes(token))) return "landscape";
  if (["狗", "猫", "动物", "宠物", "dog", "cat", "animal", "pet"].some((token) => text.includes(token))) return "animal";
  if (["女人", "女性", "女孩", "女", "woman", "female", "girl"].some((token) => text.includes(token))) return "female";
  return "portrait";
}

function isCharacterPromptSubject(subject) {
  return ["portrait", "female", "male", "child"].includes(subject);
}

function syncActiveReferenceSelectionFromDom() {
  activeReferenceCards().forEach((card) => {
    syncReferenceItemActive(
      activeReferenceKind,
      card.dataset.referenceId,
      card.classList.contains("active"),
    );
  });
}

function syncReferenceItemActive(kind, id, active) {
  const item = referenceCategories[kind]?.items.find((entry) => entry.id === id);
  if (item) {
    item.active = active;
  }
}

async function handleReferenceClick(event) {
  const button = event.target.closest(".face-reference, .reference-card");
  if (!button) return;
  if (event.target.closest('[data-action="replace-reference"]')) {
    pendingReferenceReplaceTarget = referenceReplaceTargetFromButton(button);
    pendingReferenceUploadKind = pendingReferenceReplaceTarget.kind;
    referenceUploadInput.multiple = false;
    referenceUploadInput.click();
    apiStatus.textContent = `请选择图片替换：${pendingReferenceReplaceTarget.label}`;
    return;
  }
  if (event.target.closest('[data-action="remove-reference"]')) {
    const removeAction = event.target.closest('[data-action="remove-reference"]');
    const kind = button.dataset.referenceKind || "face";
    const referenceId = button.dataset.referenceId;
    const label = button.dataset.referenceLabel || referenceCategories[kind]?.label || "参考图";
    await confirmBeforeDelete({
      key: `reference:${kind}:${referenceId}`,
      button: removeAction,
      idleText: "移除",
      confirmText: "确认",
      idleLabel: `移除参考图 ${label}`,
      confirmLabel: `确认移除参考图 ${label}`,
      statusText: `再次点击确认移除参考图：${label}`,
      onConfirm: async () => {
        removeReferenceAsset(kind, referenceId);
        if (kind === "face") {
          await syncActiveCharacterReferences(0, "参考图已移除");
        } else {
          await syncActiveReferenceCollection(kind, 0, "参考图已移除");
        }
      },
    });
    return;
  }
  if (button.classList.contains("add-face")) {
    pendingReferenceUploadKind = "face";
    pendingReferenceReplaceTarget = null;
    referenceUploadInput.multiple = true;
    referenceUploadInput.click();
    return;
  }
  if (button.classList.contains("add-reference")) {
    pendingReferenceUploadKind = activeReferenceKind;
    pendingReferenceReplaceTarget = null;
    referenceUploadInput.multiple = true;
    referenceUploadInput.click();
    return;
  }
  button.classList.toggle("active");
  const isActive = button.classList.contains("active");
  const kind = button.dataset.referenceKind || "face";
  const label = button.dataset.referenceLabel || "参考图";
  if (button.classList.contains("reference-card")) {
    syncReferenceItemActive(kind, button.dataset.referenceId, isActive);
    if (isActive && button.dataset.referencePrompt) {
      addPromptClause(button.dataset.referencePrompt);
    }
  } else if (kind === "face") {
    syncReferenceItemActive(kind, button.dataset.referenceId, isActive);
  }
  apiStatus.textContent = isActive ? `${label}参考已选中` : `${label}参考已取消`;
  if (referenceCollectionKinds.includes(kind)) {
    await syncActiveReferenceCollection(kind, 0, apiStatus.textContent);
  }
}

function referenceReplaceTargetFromButton(button) {
  const kind = button.dataset.referenceKind || "face";
  return {
    kind,
    id: button.dataset.referenceId || "",
    label: button.dataset.referenceLabel || button.dataset.ref || referenceCategories[kind]?.label || "参考图",
    faceButton: button.classList.contains("face-reference") ? button : null,
  };
}

async function uploadReferenceFiles(fileList) {
  const files = [...(fileList || [])].filter((file) => file.type.startsWith("image/"));
  if (!files.length) return;
  const uploadKind = pendingReferenceUploadKind || activeReferenceKind;

  try {
    const assets = [];
    for (const file of files) {
      const dataUrl = await readFileAsDataUrl(file);
      assets.push(await saveReferenceAsset(file, dataUrl));
    }
    if (pendingReferenceReplaceTarget && assets[0]) {
      replaceReferenceAsset(assets[0], pendingReferenceReplaceTarget);
    } else {
      assets.forEach((asset) => appendReferenceAsset(asset, uploadKind));
    }
    if (uploadKind === "face") {
      await syncActiveCharacterReferences(assets.length, pendingReferenceReplaceTarget ? "参考图已替换" : "");
    } else {
      const message = pendingReferenceReplaceTarget
        ? `${referenceCategories[uploadKind]?.label || "参考"}参考图已替换`
        : `已上传 ${assets.length} 张${referenceCategories[uploadKind]?.label || "参考"}参考图`;
      await syncActiveReferenceCollection(uploadKind, assets.length, message);
    }
  } catch (error) {
    apiStatus.textContent = error.message;
  } finally {
    pendingReferenceUploadKind = activeReferenceKind;
    pendingReferenceReplaceTarget = null;
    referenceUploadInput.multiple = true;
    referenceUploadInput.value = "";
  }
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("读取图片失败"));
    reader.readAsDataURL(file);
  });
}

async function saveReferenceAsset(file, dataUrl) {
  if (!apiAvailable) {
    return { name: file.name, path: dataUrl };
  }
  const response = await fetch("/api/assets/reference", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: file.name, data_url: dataUrl }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `上传失败：${response.status}`);
  }
  return payload.asset;
}

function appendReferenceAsset(asset, kind = "face") {
  const source = normalizeAssetPath(asset.path);
  const category = referenceCategories[kind] || referenceCategories.face;
  const item = {
    id: asset.id || asset.name || `reference-${Date.now()}`,
    label: "上传",
    image: source,
    alt: asset.name || "上传参考图",
    prompt: `${category.label}参考：沿用上传图片的${category.label}特征`,
    active: true,
  };
  if (kind === "face") {
    const faceButton = document.createElement("button");
    faceButton.className = "face-reference active";
    faceButton.type = "button";
    faceButton.dataset.referenceKind = "face";
    faceButton.dataset.referenceId = item.id;
    faceButton.dataset.referenceLabel = "上传";
    const faceImage = document.createElement("img");
    faceImage.src = displayAssetPath(source);
    faceImage.alt = asset.name || "上传参考脸";
    const faceLabel = document.createElement("span");
    faceLabel.textContent = "上传";
    const replaceAction = document.createElement("span");
    replaceAction.className = "replace-reference";
    replaceAction.dataset.action = "replace-reference";
    replaceAction.textContent = "替换";
    faceButton.append(faceImage, faceLabel, replaceAction);
    identityStrip.insertBefore(faceButton, identityStrip.querySelector(".add-face"));
  }

  category.items.push(item);
  if (activeReferenceKind === kind) {
    renderReferenceRail();
  }
  if (kind === "face") {
    renderIdentityStripFromReferences();
  }
}

function replaceReferenceAsset(asset, target) {
  const kind = target.kind || "face";
  const source = normalizeAssetPath(asset.path);
  const category = referenceCategories[kind] || referenceCategories.face;
  const nextItem = {
    id: target.id || asset.id || asset.name || `reference-${Date.now()}`,
    label: target.label || "替换",
    image: source,
    alt: asset.name || "替换参考图",
    prompt: `${category.label}参考：沿用替换图片的${category.label}特征`,
    active: true,
  };

  const itemIndex = category.items.findIndex((item) => item.id === target.id);
  if (itemIndex >= 0) {
    category.items[itemIndex] = { ...category.items[itemIndex], ...nextItem };
  } else {
    category.items.push(nextItem);
  }

  if (kind === "face") {
    const selector = nextItem.id ? `[data-reference-id="${CSS.escape(nextItem.id)}"]` : "";
    const faceButton = target.faceButton || (selector ? identityStrip.querySelector(selector) : null);
    if (faceButton) {
      faceButton.classList.add("active");
      faceButton.dataset.referenceKind = "face";
      faceButton.dataset.referenceId = nextItem.id;
      faceButton.dataset.referenceLabel = nextItem.label;
      let image = faceButton.querySelector("img");
      if (!image) {
        image = document.createElement("img");
        faceButton.prepend(image);
      }
      image.src = displayAssetPath(source);
      image.alt = asset.name || "替换参考脸";
      let label = [...faceButton.querySelectorAll("span")].find((node) => !node.classList.contains("replace-reference"));
      if (!label) {
        label = document.createElement("span");
        faceButton.append(label);
      }
      label.textContent = nextItem.label;
      if (!faceButton.querySelector(".replace-reference")) {
        const replaceAction = document.createElement("span");
        replaceAction.className = "replace-reference";
        replaceAction.dataset.action = "replace-reference";
        replaceAction.textContent = "替换";
        faceButton.append(replaceAction);
      }
    }
  }

  if (activeReferenceKind === kind) {
    renderReferenceRail();
  }
  if (kind === "face") {
    renderIdentityStripFromReferences();
  }
}

function removeReferenceAsset(kind, referenceId) {
  const category = referenceCategories[kind] || referenceCategories.face;
  if (!referenceId) return;
  category.items = category.items.filter((item) => item.id !== referenceId);
  if (category.items.length && !category.items.some((item) => item.active)) {
    category.items[0].active = true;
  }
  if (activeReferenceKind === kind) {
    renderReferenceRail();
  }
  if (kind === "face") {
    renderIdentityStripFromReferences();
  }
  apiStatus.textContent = category.items.length ? "参考图已移除" : "参考图已清空";
}

async function syncActiveReferenceCollection(kind, changeCount = 0, prefix = "") {
  if (!referenceCollectionKinds.includes(kind)) return;
  const references = referencesForCollectionSync(kind);
  const category = referenceCategories[kind] || {};

  if (!apiAvailable) {
    const character = characters.find((item) => item.id === activeCharacterId);
    if (character) {
      character.reference_collections = {
        ...(character.reference_collections || {}),
        [kind]: references,
      };
      character.asset_summary = {
        ...(character.asset_summary || {}),
        reference_collection_count: referenceCollectionKinds.reduce(
          (total, collectionKind) => total + (character.reference_collections?.[collectionKind]?.length || 0),
          0,
        ),
      };
    }
    apiStatus.textContent = prefix || `${category.label || "参考"}参考已更新`;
    return;
  }

  const response = await fetch(`/api/characters/${activeCharacterId}/reference-collections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind, references }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `参考集合同步失败：${response.status}`);
  }
  const updated = normalizeCharacter(payload.character);
  characters = characters.map((item) => (item.id === updated.id ? updated : item));
  setCharacter(updated.id);
  renderCharacterList();
  apiStatus.textContent = prefix || `${category.label || "参考"}参考已同步`;
}

async function syncActiveCharacterReferences(uploadCount, prefix = "") {
  const references = referencesForCharacterSync();
  if (!references.length) {
    apiStatus.textContent = "至少保留 1 张参考图";
    return;
  }
  const faceImages = references.map((reference) => reference.image).filter(Boolean);
  const shouldTrain = faceImages.length >= 3;

  if (!apiAvailable) {
    const character = characters.find((item) => item.id === activeCharacterId);
    if (character) {
      character.reference_assets = references;
      character.asset_summary = {
        ...(character.asset_summary || {}),
        reference_count: references.length,
      };
    }
    apiStatus.textContent = shouldTrain
      ? `${prefix || `已上传 ${uploadCount} 张参考图`} · 静态预览未保存训练`
      : `${prefix || "参考图已保存到本地界面"} · 至少需要 3 张才能训练身份`;
    return;
  }

  const character = characters.find((item) => item.id === activeCharacterId);
  const nextVersion = (character?.version || 1) + 1;
  const response = await fetch(`/api/characters/${activeCharacterId}/references`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      train: shouldTrain,
      note: `参考图资产同步 v${nextVersion}`,
      references,
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `参考图同步失败：${response.status}`);
  }
  const updated = normalizeCharacter(payload.character);
  characters = characters.map((item) => (item.id === updated.id ? updated : item));
  setCharacter(updated.id);
  renderCharacterList();
  await refreshOpenVersionHistory();
  if (payload.training_status === "trained") {
    apiStatus.textContent = `${prefix || `已上传 ${uploadCount} 张参考图`}，${updated.name} 已训练到 v${updated.version}`;
  } else if (payload.training_status === "needs_three_references") {
    apiStatus.textContent = `${prefix || "参考图已保存"}，至少需要 3 张才能训练身份`;
  } else {
    apiStatus.textContent = `${prefix || "参考图已保存"}，角色参考资产已同步`;
  }
}

function referencesForCharacterSync() {
  return referenceCategories.face.items.map((item, index) => ({
    id: item.id || `face-${index + 1}`,
    label: item.label || `参考 ${index + 1}`,
    image: normalizeAssetPath(item.image || item.source || ""),
    source: normalizeAssetPath(item.source || item.image || ""),
    prompt: item.prompt || "保持同一角色身份",
    active: Boolean(item.active ?? index === 0),
    created_at: item.created_at || "",
    updated_at: new Date().toISOString(),
  })).filter((item) => item.image);
}

function referencesForCollectionSync(kind) {
  return (referenceCategories[kind]?.items || []).map((item, index) => ({
    id: item.id || `${kind}-${index + 1}`,
    label: item.label || `参考 ${index + 1}`,
    image: normalizeAssetPath(item.image || item.source || ""),
    source: normalizeAssetPath(item.source || item.image || ""),
    visual: item.visual || "",
    alt: item.alt || item.label || "参考图",
    prompt: item.prompt || "",
    active: Boolean(item.active),
    created_at: item.created_at || "",
    updated_at: new Date().toISOString(),
  })).filter((item) => item.image || item.visual);
}

function renderLoraSelect() {
  const current = loraSelect.value || "portrait-consistency";
  loraSelect.replaceChildren(
    ...loras.map((lora) => {
      const option = document.createElement("option");
      option.value = lora.id;
      option.textContent = lora.label || lora.name;
      return option;
    }),
  );
  applyLoraSelection(loras.some((lora) => lora.id === current) ? current : loras[0]?.id, false);
}

function applyLoraSelection(loraId, announce = false, weightOverride = undefined) {
  const selected = loras.find((lora) => lora.id === loraId) || loras[0] || fallbackLoras[0];
  if (!selected) return;
  loraSelect.value = selected.id;
  const nextWeight = weightOverride ?? selected.default_weight ?? selected.weight ?? 0.6;
  syncLoraWeight(nextWeight);
  loraBadge.textContent = selected.label || selected.name;
  if (announce) {
    apiStatus.textContent = `LoRA 已切换：${selected.label || selected.name}`;
  }
}

function syncLoraWeight(value) {
  const displayValue = Number(value).toFixed(2);
  loraRange.value = displayValue;
  loraValue.textContent = displayValue;
  loraValue.value = displayValue;
  loraValue.setAttribute("aria-label", `LoRA 权重 ${displayValue}`);
}

function setActiveButton(buttons, activeButton) {
  buttons.forEach((button) => {
    button.classList.toggle("active", button === activeButton);
  });
}

function normalizeAccountState(account = {}) {
  const requestedPlanId = account.plan_id || account.id || "free";
  const plan = fallbackAccountPlans.find((item) => item.id === requestedPlanId) || fallbackAccountPlans[0];
  const monthlyCredits = Number(account.monthly_credits ?? account.credits ?? plan.monthly_credits ?? plan.credits ?? 1200);
  const creditsRemaining = Number(account.credits_remaining ?? monthlyCredits);
  return {
    plan_id: plan.id,
    label: account.label || plan.label,
    badge: account.badge || plan.badge,
    user_segment: account.user_segment || plan.user_segment,
    monthly_credits: monthlyCredits,
    credits_remaining: Math.max(0, creditsRemaining),
    credits_used: Math.max(0, Number(account.credits_used || 0)),
    cost_per_image: Number(account.cost_per_image || plan.cost_per_image || 2),
    features: Array.isArray(account.features) ? account.features : plan.features,
    billing_cycle: account.billing_cycle || "monthly",
    updated_at: account.updated_at || "",
  };
}

function setAccountState(account, plans = accountPlans) {
  accountPlans = Array.isArray(plans) && plans.length ? plans : fallbackAccountPlans;
  accountState = normalizeAccountState(account);
  activePlanId = accountState.plan_id || "free";
  if (activePlanId === "free") {
    window.localStorage.removeItem(subscriptionKey);
  } else {
    window.localStorage.setItem(subscriptionKey, activePlanId);
  }
  applySubscriptionState();
  updateGenerateSummary();
}

async function loadAccount() {
  if (!apiAvailable) {
    setAccountState({ plan_id: activePlanId });
    return;
  }
  const response = await fetch("/api/account");
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  const payload = await response.json();
  setAccountState(payload.account, payload.plans);
}

async function activatePlan(planId) {
  if (!demoPlans[planId]) return;
  if (apiAvailable) {
    try {
      const response = await fetch("/api/account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || `API ${response.status}`);
      }
      setAccountState(payload.account, payload.plans);
      apiStatus.textContent = `${accountState.label} 已启用 · 后端额度 ${accountState.credits_remaining}`;
      return;
    } catch (error) {
      apiStatus.textContent = error.message;
      return;
    }
  }

  setAccountState({ plan_id: planId });
  apiStatus.textContent = `${accountState.label} 已启用 · 本地演示额度 ${accountState.credits_remaining}`;
}

function applySubscriptionState() {
  accountState = normalizeAccountState(accountState);
  creditPill.textContent = String(accountState.credits_remaining);
  if (accountState.plan_id === "free") {
    upgradeButton.textContent = "升级";
    upgradeButton.classList.remove("active");
    return;
  }
  upgradeButton.textContent = accountState.badge;
  upgradeButton.classList.add("active");
}

function currentPlanExport() {
  return {
    plan_id: accountState.plan_id || "free",
    label: accountState.label || "免费版",
    credits: Number(accountState.credits_remaining || 0),
    monthly_credits: Number(accountState.monthly_credits || 0),
    credits_used: Number(accountState.credits_used || 0),
    user_segment: accountState.user_segment || "普通用户",
  };
}

function projectCharacterNames(project) {
  return projectCharacters(project).map((character) => character.name || character.id);
}

function projectStatusLabel(status) {
  const labels = {
    draft: "草稿",
    active: "进行中",
    in_review: "审阅中",
    approved: "已批准",
    archived: "已归档",
  };
  return labels[status] || "进行中";
}

function projectLicenseLabel(project) {
  const status = project?.ip_package?.license_status || project?.review?.license_status || "";
  const labels = {
    "commercial-ready": "可商用发布",
    "creator-ready": "可创作者发布",
    "pending-review": "待授权确认",
    draft: "草稿未提交",
    "internal-active": "内部进行中",
  };
  return labels[status] || (project?.status === "approved" ? "可发布" : "待审阅");
}

function projectReviewActionLabel(action) {
  return {
    submit_review: "项目已提交审阅",
    approve: "项目已批准发布",
    withdraw_review: "项目已撤回草稿",
  }[action] || "项目审阅状态已更新";
}

function lastUsedLabel(value) {
  return value ? `最近 ${compactDateTime(value)}` : "未使用";
}

function assetMetaForCharacter(character) {
  const summary = character.asset_summary || {};
  return [
    `${Number(summary.version_count || character.version || 1)} 版本`,
    `${Number(summary.generation_count || 0)} 图`,
    `${Number(summary.favorite_count || 0)} 收藏`,
    lastUsedLabel(summary.last_used_at),
  ].join(" · ");
}

function compactDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function compactPath(value) {
  const parts = String(value || "").split(/[\\/]/).filter(Boolean);
  if (!parts.length) return "";
  return parts.slice(-2).join("/");
}

function applyLocalProjectReview(project, action) {
  const now = new Date().toISOString();
  const next = {
    ...project,
    review: { ...(project.review || {}) },
    ip_package: project.ip_package ? { ...project.ip_package } : null,
  };
  if (action === "submit_review") {
    next.status = "in_review";
    next.submitted_at = now;
    next.approved_at = null;
    next.reviewed_by = null;
  }
  if (action === "approve") {
    next.status = "approved";
    next.submitted_at = next.submitted_at || now;
    next.approved_at = now;
    next.reviewed_by = "local-reviewer";
  }
  if (action === "withdraw_review") {
    next.status = "draft";
    next.approved_at = null;
    next.reviewed_by = null;
  }
  const licenseStatus = next.status === "approved"
    ? (next.user_segment === "商业用户" ? "commercial-ready" : "creator-ready")
    : next.status === "in_review"
      ? "pending-review"
      : next.status === "draft"
        ? "draft"
        : "internal-active";
  next.review = {
    ...next.review,
    status: next.status,
    label: projectStatusLabel(next.status),
    license_status: licenseStatus,
    release_ready: next.status === "approved",
    submitted_at: next.submitted_at,
    approved_at: next.approved_at,
    reviewed_by: next.reviewed_by,
  };
  if (next.ip_package) {
    next.ip_package = {
      ...next.ip_package,
      license_status: licenseStatus,
      release_ready: next.status === "approved",
      review: next.review,
    };
  }
  return next;
}

function downloadJson(payload, filename) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function initializeReferenceOrdering() {
  updateReferenceDraggables();

  referenceList.addEventListener("dragstart", (event) => {
    const card = event.target.closest(".reference-card");
    if (!card || card.classList.contains("add-reference")) {
      event.preventDefault();
      return;
    }
    draggedReferenceCard = card;
    draggedReferenceOriginalIndex = activeReferenceCards().indexOf(card);
    card.classList.add("is-dragging");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", card.dataset.referenceId || "reference-card");
  });

  referenceList.addEventListener("dragover", (event) => {
    if (!draggedReferenceCard) return;
    const target = event.target.closest(".reference-card");
    if (!target || target === draggedReferenceCard || target.classList.contains("add-reference")) return;
    event.preventDefault();
    const box = target.getBoundingClientRect();
    const insertBeforeTarget = event.clientX < box.left + box.width / 2;
    referenceList.insertBefore(draggedReferenceCard, insertBeforeTarget ? target : target.nextSibling);
  });

  referenceList.addEventListener("drop", (event) => {
    if (!draggedReferenceCard) return;
    event.preventDefault();
    const target = event.target.closest(".reference-card");
    if (target && target !== draggedReferenceCard && !target.classList.contains("add-reference")) {
      const targetIndex = activeReferenceCards().filter((card) => card !== draggedReferenceCard).indexOf(target);
      const shouldInsertAfter = draggedReferenceOriginalIndex <= targetIndex;
      referenceList.insertBefore(draggedReferenceCard, shouldInsertAfter ? target.nextSibling : target);
    }
    completeReferenceDrag("参考图顺序已更新");
  });

  referenceList.addEventListener("dragend", () => {
    completeReferenceDrag();
  });
}

function completeReferenceDrag(message = "") {
  if (draggedReferenceCard) {
    draggedReferenceCard.classList.remove("is-dragging");
  }
  syncActiveReferenceOrder();
  draggedReferenceCard = null;
  draggedReferenceOriginalIndex = -1;
  updateReferenceDraggables();
  if (message) {
    apiStatus.textContent = message;
  }
  if (message && referenceCollectionKinds.includes(activeReferenceKind)) {
    void syncActiveReferenceCollection(activeReferenceKind, 0, message);
  }
}

function syncActiveReferenceOrder() {
  const category = referenceCategories[activeReferenceKind];
  if (!category) return;
  const byId = new Map(category.items.map((item) => [item.id, item]));
  const ordered = activeReferenceCards().map((card) => byId.get(card.dataset.referenceId)).filter(Boolean);
  const missing = category.items.filter((item) => !ordered.includes(item));
  category.items = [...ordered, ...missing];
}

function updateReferenceDraggables() {
  activeReferenceCards().forEach((card, index) => {
    card.draggable = true;
    card.dataset.referenceId = card.dataset.referenceId || `reference-${index + 1}`;
    card.setAttribute("aria-label", `${card.querySelector("img")?.alt || "参考图"} 第 ${index + 1} 位`);
  });
}

function setResultView(view) {
  const isList = view === "list";
  outputGrid.classList.toggle("list-view", isList);
  gridViewButton.classList.toggle("active", !isList);
  listViewButton.classList.toggle("active", isList);
  apiStatus.textContent = isList ? "已切换到列表视图" : "已切换到网格视图";
}

function openAdvancedPanel() {
  advancedPanel.hidden = false;
  advancedToggle.setAttribute("aria-expanded", "true");
}

function ensureReferenceEnabled() {
  referenceToggle.setAttribute("aria-pressed", "true");
  referenceToggle.classList.add("is-on");
  document.querySelector(".face-card")?.classList.remove("is-disabled");
}

function addPromptClause(clause) {
  if (!promptInput.value.includes(clause)) {
    promptInput.value = `${promptInput.value}，${clause}`;
    updatePromptCounters();
  }
}

function addNegativeClause(clause) {
  if (!negativePromptInput.value.includes(clause)) {
    negativePromptInput.value = `${negativePromptInput.value}，${clause}`;
    updatePromptCounters();
  }
}

function stylePresetPillLabels(item) {
  const controlLabels = styleCatalogControlRows(item)
    .map((row) => row?.value || row?.label)
    .filter(Boolean)
    .slice(0, 2);
  return [
    item.label,
    ...controlLabels,
    labelForLora(item.loraId) || item.loraId,
  ].filter(Boolean);
}

function applyStylePreset(style) {
  const item = styleCatalogItem(style);
  const promptSnippet = item.promptSnippet;
  syncStyle(item.styleWeight);
  applyLoraSelection(item.loraId, false, item.loraWeight);
  if (promptSnippet && !promptInput.value.includes(promptSnippet)) {
    promptInput.value = `${promptInput.value}，${promptSnippet}`;
    updatePromptCounters();
  }
  activeStyleLibraryLabel = item.label;
  setActiveStyleSwatch(item.label);
  stylePills.replaceChildren(...stylePresetPillLabels(item).map((label) => pill(label)));
  apiStatus.textContent = `风格已切换：${item.label}`;
}

function setActiveStyleFromPreset(preset, loraId) {
  const byLora = loraId && styleCatalog.find((item) => item.loraId === loraId);
  if (byLora) {
    setActiveStyleSwatch(byLora.label);
    return;
  }
  const presetMap = {
    anime: "动漫",
    commercial: "商业广告",
    cinematic: "写真",
  };
  setActiveStyleSwatch(presetMap[preset] || "写真");
}

function setActiveStyleSwatch(label) {
  const canonicalLabel = canonicalStyleLabel(label);
  const buttons = stylePresetGrid.querySelectorAll(".style-swatch");
  buttons.forEach((button) => {
    button.classList.toggle("active", canonicalStyleLabel(button.dataset.style) === canonicalLabel);
  });
}

function labelForLora(loraId) {
  const lora = loras.find((item) => item.id === loraId) || fallbackLoras.find((item) => item.id === loraId);
  return lora?.label || "";
}

function downloadGeneration(generation) {
  const link = document.createElement("a");
  link.href = imageForGeneration(generation, generation.variant || 1);
  link.download = `${generation.character_name || "persona"}-${generation.id || "generation"}.png`;
  link.click();
  apiStatus.textContent = "生成图下载已触发";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

function imageForGeneration(generation, index = 0) {
  const image = generation?.image || "";
  if (image && !image.includes("lina-morning.svg")) {
    return image;
  }
  const variant = Number(generation?.variant || index + 1);
  return `assets/persona-ref-${((variant - 1) % 4) + 1}.png`;
}

function getCheckedValue(name) {
  return document.querySelector(`input[name="${name}"]:checked`)?.value;
}

function presetClass(preset) {
  if (preset === "anime") return "anime";
  if (preset === "commercial") return "commercial";
  return "";
}

function labelForPreset(preset) {
  if (preset === "anime") return "动漫";
  if (preset === "commercial") return "商业广告";
  return "写真";
}

function labelForDrift(risk) {
  if (risk === "low") return "低";
  if (risk === "medium") return "中";
  if (risk === "high") return "高";
  if (risk === "not_applicable") return "不适用";
  return "未知";
}

function poseControlLabel(pose) {
  return {
    auto: "自动",
    front: "正面",
    "three-quarter": "四分之三侧脸",
    side: "侧脸",
    reference_pose: "参考姿态",
  }[pose] || "自动";
}

function pill(text) {
  const element = document.createElement("span");
  element.textContent = text;
  return element;
}
