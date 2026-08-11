# marketing-agent 프런트엔드 (Next.js standalone).

# ── 의존성 ─────────────────────────────────────────────────────
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# npm ci는 package-lock.json을 그대로 따른다 — 이미지가 재현된다.
RUN npm ci

# ── 빌드 ───────────────────────────────────────────────────────
FROM node:22-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 브라우저가 백엔드를 부를 주소.
#
# **빌드 시점 인자여야 한다.** NEXT_PUBLIC_*는 next build가 클라이언트 번들에
# 문자열로 박아 넣는다 — 런타임 environment:로 주면 서버 프로세스 환경만
# 바뀌고 브라우저 번들은 그대로다.
ARG NEXT_PUBLIC_API_BASE=http://localhost:8012
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE

RUN npm run build

# ── 런타임 ─────────────────────────────────────────────────────
FROM node:22-slim
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV NODE_ENV=production \
    PORT=3011 \
    HOSTNAME=0.0.0.0

# node 사용자(uid 1000)는 이미지에 이미 있다.
# standalone은 실행에 필요한 것만 담는다 — devDependencies는 들어오지 않는다.
COPY --from=build --chown=node:node /app/.next/standalone ./
# public과 .next/static은 standalone이 자동 복사하지 않는다.
COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/.next/static ./.next/static

USER node
EXPOSE 3011

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3011/ > /dev/null || exit 1

CMD ["node", "server.js"]
