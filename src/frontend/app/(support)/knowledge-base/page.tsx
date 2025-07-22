'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog";
import { Plus, Edit, Eye, Tag, Clock, User, Trash2, X } from "lucide-react";
import { SearchBar } from "@/components/ui";
import AddArticleForm from '@/components/ui/support/knowledgeBase/AddArticleForm';
import EditArticleForm from '@/components/ui/support/knowledgeBase/EditArticleForm';

interface Article {
  id: string;
  title: string;
  category: string;
  status: string;
  author: string;
  updated: string;
  views: number;
  excerpt: string;
  tags: string[];
}

const initialArticles: Article[] = [
  {
    id: "KB001",
    title: "How to Reset Your Password",
    category: "Account Management",
    status: "published",
    author: "Sarah Chen",
    updated: "2 days ago",
    views: 1247,
    tags: ["password", "security", "account"],
    excerpt: "Step-by-step guide to resetting your account password through various methods.",
  },
  {
    id: "KB002",
    title: "Payment Processing Troubleshooting",
    category: "Billing",
    status: "draft",
    author: "Mike Johnson",
    updated: "1 hour ago",
    views: 892,
    tags: ["payment", "billing", "troubleshooting"],
    excerpt: "Common payment issues and their solutions for customers experiencing checkout problems.",
  },
  {
    id: "KB003",
    title: "Premium Features Overview",
    category: "Features",
    status: "published",
    author: "Lisa Wang",
    updated: "1 week ago",
    views: 2156,
    tags: ["premium", "features", "upgrade"],
    excerpt: "Complete guide to premium features and how to make the most of your subscription.",
  },
];

const totalStats = [
  { name: "Top Articles", count: 134 },
  { name: "Published", count: 108 },
  { name: "Views", count: 24.3 },
];

const categories = [
  { name: "Account Management", count: 24 },
  { name: "Billing", count: 18 },
  { name: "Features", count: 32 },
  { name: "Troubleshooting", count: 45 },
  { name: "API Documentation", count: 15 },
];

const statusColors = {
  published: "bg-green-100 text-green-800",
  draft: "bg-yellow-100 text-yellow-800",
  archived: "bg-gray-100 text-gray-800",
};

export default function Knowledge() {
  const [articles, setArticles] = useState<Article[]>(initialArticles);

  const handleAddArticle = (data: Article) => {
    setArticles([...articles, data]);
  };

  const handleEditArticle = (data: Article) => {
    setArticles(articles.map((article) => (article.id === data.id ? data : article)));
  };

  const handleDeleteArticle = (id: string) => {
    setArticles(articles.filter((article) => article.id !== id));
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-6 pt-0 space-y-6">
        <div className="p-4 pt-0 flex justify-end items-center gap-4 flex-wrap">
          <SearchBar placeholder="Search articles..." className="w-full sm:w-72" />
          <Dialog>
            <DialogTrigger asChild>
              <Button className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105 gap-2 text-sm whitespace-nowrap">
                <Plus className="h-4 w-4" /> New Article
              </Button>
            </DialogTrigger>
            <AddArticleForm onAddArticle={handleAddArticle} />
          </Dialog>
        </div>
        <div className="grid gap-6 lg:grid-cols-4">
          {/* Categories Sidebar */}
          <Card className="shadow-card">
            <CardContent className="space-y-2">
              <div className="space-y-2">
                {totalStats.map((stat) => (
                  <div
                    key={stat.name}
                    className="flex justify-between items-center p-2 rounded-lg hover:bg-muted/50 cursor-pointer"
                  >
                    <span className="text-sm font-medium">{stat.name}</span>
                    <Badge variant="secondary" className="text-xs">{stat.count}</Badge>
                  </div>
                ))}
              </div>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 pt-6">
                  <Tag className="h-5 w-5" />
                  Categories
                </CardTitle>
              </CardHeader>
              <div className="space-y-2">
                {categories.map((category) => (
                  <div
                    key={category.name}
                    className="flex justify-between items-center p-2 rounded-lg hover:bg-muted/50 cursor-pointer"
                  >
                    <span className="text-sm font-medium">{category.name}</span>
                    <Badge variant="secondary" className="text-xs">{category.count}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Articles List */}
          <div className="lg:col-span-3 space-y-6">
            <Tabs defaultValue="all" className="space-y-4">
              <TabsList>
                <TabsTrigger value="all">All Articles</TabsTrigger>
                <TabsTrigger value="published">Published</TabsTrigger>
                <TabsTrigger value="draft">Drafts</TabsTrigger>
              </TabsList>
              {["all", "published", "draft"].map((status) => {
                const filteredArticles =
                  status === "all" ? articles : articles.filter((a) => a.status === status);

                return (
                  <TabsContent key={status} value={status}>
                    <Card className="shadow-card">
                      <CardContent className="p-0">
                        {filteredArticles.length > 0 ? (
                          <div className="divide-y divide-border">
                            {filteredArticles.map((article) => (
                              <div key={article.id} className="p-6 hover:bg-muted/50 transition-colors">
                                <div className="flex items-start justify-between gap-4">
                                  <div className="flex-1 min-w-0 space-y-3">
                                    <div className="flex items-center gap-2">
                                      <Badge className={`text-xs ${statusColors[article.status as keyof typeof statusColors]}`}>
                                        {article.status}
                                      </Badge>
                                      <Badge variant="outline" className="text-xs">
                                        {article.category}
                                      </Badge>
                                    </div>
                                    <div>
                                      <h3 className="font-semibold text-foreground mb-1">{article.title}</h3>
                                      <p className="text-sm text-muted-foreground">{article.excerpt}</p>
                                    </div>
                                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                      <div className="flex items-center gap-1">
                                        <User className="h-3 w-3" />
                                        {article.author}
                                      </div>
                                      <div className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        Updated {article.updated}
                                      </div>
                                      <div className="flex items-center gap-1">
                                        <Eye className="h-3 w-3" />
                                        {article.views} views
                                      </div>
                                    </div>
                                    <div className="flex gap-1">
                                      {article.tags.map((tag) => (
                                        <Badge key={tag} variant="outline" className="text-xs">
                                          #{tag}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                  <div className="flex gap-2">
                                    <Dialog>
                                      <DialogTrigger asChild>
                                        <Button variant="ghost" size="sm">
                                          <Eye className="h-4 w-4" />
                                        </Button>
                                      </DialogTrigger>
                                      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                                        <DialogHeader>
                                          <DialogTitle className="text-black dark:text-white">{article.title}</DialogTitle>
                                        </DialogHeader>
                                        <DialogClose
                                          className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
                                        >
                                          <X className="h-4 w-4 text-black dark:text-white" />
                                          <span className="sr-only">Close</span>
                                        </DialogClose>
                                        <div className="space-y-4 py-4">
                                          <div className="flex gap-2">
                                            <Badge className={`text-xs ${statusColors[article.status as keyof typeof statusColors]}`}>
                                              {article.status}
                                            </Badge>
                                            <Badge variant="outline" className="text-xs">
                                              {article.category}
                                            </Badge>
                                          </div>
                                          <div className="grid grid-cols-2 gap-4">
                                            <div>
                                              <Label className="text-sm font-medium text-muted-foreground">Author</Label>
                                              <p className="text-sm text-black dark:text-white">{article.author}</p>
                                            </div>
                                            <div>
                                              <Label className="text-sm font-medium text-muted-foreground">Last Updated</Label>
                                              <p className="text-sm text-black dark:text-white">{article.updated}</p>
                                            </div>
                                            <div>
                                              <Label className="text-sm font-medium text-muted-foreground">Views</Label>
                                              <p className="text-sm text-black dark:text-white">{article.views}</p>
                                            </div>
                                            <div>
                                              <Label className="text-sm font-medium text-muted-foreground">Tags</Label>
                                              <p className="text-sm text-black dark:text-white">{article.tags.join(', ')}</p>
                                            </div>
                                          </div>
                                          <div>
                                            <Label className="text-sm font-medium text-muted-foreground">Excerpt</Label>
                                            <p className="text-sm mt-1 p-3 bg-muted/50 rounded-lg text-black dark:text-white">
                                              {article.excerpt}
                                            </p>
                                          </div>
                                          <div className="prose max-w-none text-black dark:text-white">
                                            <p>This is a preview of the knowledge base article content...</p>
                                          </div>
                                        </div>
                                      </DialogContent>
                                    </Dialog>
                                    <Dialog>
                                      <DialogTrigger asChild>
                                        <Button variant="ghost" size="sm">
                                          <Edit className="h-4 w-4" />
                                        </Button>
                                      </DialogTrigger>
                                      <EditArticleForm article={article} onEditArticle={handleEditArticle} />
                                    </Dialog>
                                    <Dialog>
                                      <DialogTrigger asChild>
                                        <Button variant="ghost" size="sm">
                                          <Trash2 className="h-4 w-4 text-red-500" />
                                        </Button>
                                      </DialogTrigger>
                                      <DialogContent className="max-w-md">
                                        <DialogHeader>
                                          <DialogTitle className="text-black dark:text-white">Delete Article: {article.id}</DialogTitle>
                                        </DialogHeader>
                                        <DialogClose
                                          className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
                                        >
                                          <X className="h-4 w-4 text-black dark:text-white" />
                                          <span className="sr-only">Close</span>
                                        </DialogClose>
                                        <div className="space-y-4">
                                          <p className="text-sm text-muted-foreground">
                                            Are you sure you want to delete article {article.id}? This action cannot be undone.
                                          </p>
                                          <div className="flex justify-end gap-2">
                                            <DialogClose asChild>
                                              <Button variant="outline">Cancel</Button>
                                            </DialogClose>
                                            <DialogClose asChild>
                                              <Button
                                                className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105"
                                                onClick={() => handleDeleteArticle(article.id)}
                                              >
                                                Delete
                                              </Button>
                                            </DialogClose>
                                          </div>
                                        </div>
                                      </DialogContent>
                                    </Dialog>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="p-6 text-sm text-muted-foreground">No articles found.</div>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>
                );
              })}
            </Tabs>
          </div>
        </div>
      </main>
    </div>
  );
}