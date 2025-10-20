namespace CouchTomato.Core.DTOs;

public class MovieDto
{
    public Guid ID { get; set; }
    public string Title { get; set; } = string.Empty;
    public int? Year { get; set; }
    public string? Status { get; set; }
}
