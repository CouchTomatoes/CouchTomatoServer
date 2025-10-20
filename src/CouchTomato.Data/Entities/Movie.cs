namespace CouchTomato.Data.Entities;

public class Movie : IEntityBase
{
    public Guid ID { get; set; } = Guid.NewGuid();
    public long KeyID { get; set; }
    public string Title { get; set; } = string.Empty;
    public int? Year { get; set; }
    public string? Status { get; set; } = "Wanted";

    // Base fields
    public DateTime CreatedDate { get; set; } = DateTime.UtcNow;
    public DateTime ModifiedDate { get; set; } = DateTime.UtcNow;
    public long? CreatedDateUnix { get; set; } = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
    public long? ModifiedDateUnix { get; set; } = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
    public Guid? CreatedBy { get; set; }
    public bool IsDeleted { get; set; }
}
