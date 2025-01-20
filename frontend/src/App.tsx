import axios from "axios"
import { useState } from "react"
import { Button } from "./components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card"
import { Input } from "./components/ui/input"

export default function MovieRecommendationSystem() {
    const [movies, setMovies] = useState(["", ""])
    const [recommendations, setRecommendations] = useState<string[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [message, setMessage] = useState<string | null>(null)

    const handleInputChange = (index: number, value: string) => {
        const newMovies = [...movies]
        newMovies[index] = value
        setMovies(newMovies)
    }

    const handleAddInput = () => {
        setMovies([...movies, ""])
    }

    const handleRemoveInput = (index: number) => {
        const newMovies = movies.filter((_, i) => i !== index)
        setMovies(newMovies)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setMessage(null)
        setRecommendations([])
        try {
            const filteredMovies = movies.filter((movie) => movie.trim() !== "")
            if (filteredMovies.length === 0) {
                throw new Error("Please enter at least one movie title")
            }
            const response = await axios.post("http://localhost:8000/recommendations", {
                movies: filteredMovies,
            })
            setRecommendations(response.data.recommendations)
            if (response.data.message) {
                setMessage(response.data.message)
            }
        } catch (error) {
            console.error("Error fetching recommendations:", error)
            setError(error instanceof Error ? error.message : "An error occurred while fetching recommendations")
        }
        setLoading(false)
    }

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
            <Card className="w-full max-w-2xl">
                <CardHeader>
                    <CardTitle>Movie Recommendation System</CardTitle>
                    <CardDescription>Enter movie titles to get personalized recommendations</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {movies.map((movie, index) => (
                            <div key={index} className="flex space-x-2">
                                <Input
                                    type="text"
                                    value={movie}
                                    onChange={(e) => handleInputChange(index, e.target.value)}
                                    placeholder={`Enter movie title ${index + 1}`}
                                    className="flex-grow"
                                />
                                {index > 0 && (
                                    <Button type="button" variant="destructive" onClick={() => handleRemoveInput(index)}>
                                        Remove
                                    </Button>
                                )}
                            </div>
                        ))}
                        <div className="flex justify-between">
                            <Button type="button" onClick={handleAddInput}>
                                Add Movie
                            </Button>
                            <Button type="submit" disabled={loading}>
                                {loading ? "Loading..." : "Get Recommendations"}
                            </Button>
                        </div>
                    </form>
                    {error && (
                        <div className="mt-4 text-red-600">
                            {error}
                        </div>
                    )}
                    {message && (
                        <div className="mt-4 text-blue-600">
                            {message}
                        </div>
                    )}
                    {recommendations.length > 0 && (
                        <div className="mt-8">
                            <h3 className="text-lg font-semibold mb-2">Recommendations:</h3>
                            <ul className="list-disc list-inside">
                                {recommendations.map((movie, index) => (
                                    <li key={index}>{movie}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
