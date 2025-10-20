using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using CouchTomato.Data.Entities;

namespace CouchTomato.Data.Configurations;

public class MovieConfiguration : EntityBaseConfiguration<Movie>
{
    public override void Configure(EntityTypeBuilder<Movie> builder)
    {
        builder.ToTable("Movies");

        builder.HasKey(x => x.KeyID);

        builder.Property(x => x.Title)
               .HasMaxLength(250)
               .IsRequired();

        builder.Property(x => x.CreatedDate)
               .HasColumnType("datetime2");

        builder.Property(x => x.ModifiedDate)
               .HasColumnType("datetime2");

        builder.Property(x => x.IsDeleted)
               .HasDefaultValue(false);
    }
}
