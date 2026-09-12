import type { Icons } from 'astro-pure/libs'

interface NavigationLink {
  title: string
  link: string
  icon: keyof typeof Icons
}

export interface NavigationItem extends NavigationLink {
  children?: NavigationLink[]
}

export const navigation: NavigationItem[] = [
  { title: '首页', link: '/', icon: 'earth' },
  {
    title: '文章', link: '/blog', icon: 'document',
    children: [
      { title: '全部文章', link: '/blog', icon: 'document' },
      { title: '归档', link: '/archives', icon: 'calendar' },
      { title: '标签', link: '/tags', icon: 'hashtag' }
    ]
  },
  { title: '项目', link: '/projects', icon: 'package' },
  { title: '友链', link: '/links', icon: 'link' },
  { title: '关于', link: '/about', icon: 'info' },
  {
    title: '链接', link: 'https://github.com/zszz3', icon: 'link',
    children: [
      { title: 'GitHub', link: 'https://github.com/zszz3', icon: 'github-circle' }
    ]
  }
]
